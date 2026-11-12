# UI smoothness on r2: GPU check and quick settings / launcher jank

Image `lineage_vantage-20261111-r2` (system.img SHA-256 `5a007af9…69db9`), running as a DSU guest on
stock A171WVH.21-16-16, 2026-11-11. Measured over adb as the shell user (no root): `dumpsys
SurfaceFlinger`, `dumpsys gfxinfo <package> framestats`, a 75 s Perfetto trace (sched, cpufreq, gfx/view/input
atrace, SurfaceFlinger frame timeline) and sysfs `time_in_state`, while a script pulled the quick settings
shade down and up four times and opened, scrolled and closed the launcher's app drawer four times
(`input swipe`, screen unlocked without credential). **Hardware-tested** where a number is given below.

## The GPU works

| What | Result |
|---|---|
| SurfaceFlinger RenderEngine | Skia GLES: `Qualcomm, Adreno (TM) 829, OpenGL ES 3.2 V@0842.43.1` |
| SystemUI, Launcher3 renderer | `Pipeline=Skia (Vulkan)` (`ro.hwui.use_vulkan=true`, `ro.hardware.vulkan=adreno`) |
| App GPU time per frame | p50 6-7 ms, p99 13-20 ms |
| KGSL | `gpu_model` = Adreno829 |

`Pipeline Cache: inactive` in gfxinfo only means HWUI's `separate_pipeline_cache` flag is off; the
pipeline data then lives in the ordinary shader cache.

## Jank comes from blur

| Run | SystemUI janky / p50 | Launcher janky / p50 | Consecutive frames shown one vsync apart | SF frames missed (GPU) |
|---|---|---|---|---|
| r2 as installed (window blurs on) | 40.7 % / 32 ms | 40.5 % / 22 ms | SystemUI 0 % (96 % two vsyncs apart: 60 fps) | 942 |
| `disable_window_blurs=1` | 2.2 % / 8 ms | 1.1 % / 6 ms | SystemUI 96 %, launcher 84 % | 54 |
| `cmd power set-fixed-performance-mode-enabled true` | 45 % / 34 ms | 39 % / 23 ms | SystemUI 0 % | 986 |

Both settings were reverted after their run.

With the shade or the app drawer blurred, every visible layer is composited by the GPU
(`Comp Type CLIENT` for all six layers). SurfaceFlinger's main thread then spends per frame about
prepareFrame 1.6 ms, RenderEngine drawLayers 1.7 ms, flush 0.7 ms, finishFrame 2.4 ms and `present`
4.8 ms (present blocks until the GPU finishes: same count and average as the "GPU completion" wait),
roughly 10.5 ms. The vendor sets `debug.sf.use_phase_offsets_as_durations=0` and no offsets, so AOSP's
SurfaceFlinger runs on default phase offsets: wake 1 ms after vsync, present at the next vsync, 7.3 ms
at 120 Hz. Every other frame misses; apps then block in `dequeueBuffer` (p50 13 ms in SystemUI) and the
frame timeline reports "SurfaceFlinger Stuffing".

The CPU never speeds up for this: in the traced run cpu0-5 spent about 90 % of the time at 556 MHz
(maximum 3.32 GHz) and cpu6-7 stayed at their 806 MHz floor, nearly idle. No core is saturated, so the
WALT governor sees no reason to ramp; stock gets its speed from boosts this ROM lacks:

* stock's SurfaceFlinger is Qualcomm's (`libdolphin.so` frame pacing and boost, `liblayerext.qti.so`,
  `IDisplayConfig`); the vendor's `debug.sf.{late,early,earlyGl}.{sf,app}.duration` values (10.5 ms /
  13.67 ms) are only used by AOSP's SurfaceFlinger in work-duration mode;
* stock's framework boot class path has `QPerformance.jar` and `UxPerformance.jar` (perf HAL hints on
  touch, scroll and launch);
* stock's system_ext labels `vendor.mpctl.init.complete` `vendor_wlc_public_prop`; here it fell under
  `vendor_default_prop` and the perf HAL's write was denied at boot
  (`avc: denied { set } … scontext=vendor_hal_perf_default tcontext=vendor_default_prop`);
* SurfaceFlinger's ADPF CPU hint session is off (`use_adpf_cpu_hint: false`), although the vendor's
  power HAL supports hint sessions (`Hint Session Support: true`) and may set scheduling of
  surfaceflinger.

Fixed-performance mode changes nothing (the power HAL does not act on it). The UI processes sit in the
expected cgroups (launcher `top-app`, SystemUI `foreground`; the vendor's uclamp settings are the
stock ones).

## Changes in r3 (built and checked statically, not yet measured)

* `debug.sf.use_phase_offsets_as_durations=1` in `/product/etc/build.prop` (read after the vendor's =0):
  SurfaceFlinger uses the vendor's work durations (10.5 ms for itself, 13.67 ms for apps), so a
  GPU-composited frame has more than one vsync. About one frame of extra latency.
* `debug.sf.enable_adpf_cpu_hint=true`: SurfaceFlinger's ADPF hint session.
* `vendor_wlc_public_prop` with stock's 202504 mapping and property_contexts line.

Immediate workaround on r2 without a new image: Developer options, "Allow window-level blurs" off.
