import cv2
import numpy as np
import json
import os
from scipy.ndimage import uniform_filter1d

def detect_truck_events(video_path, imu_path=None):
    """
    Detecta intercambios de camión.
    Estrategia: IMU (giroscopio) → idle del operador = intercambio.
    Fallback: video motion diff si no hay IMU.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"Video: {total_frames} frames @ {fps:.1f}fps = {total_frames/fps:.0f}s")

    # ── Intentar detección por IMU primero (más robusta) ──
    if imu_path and os.path.exists(imu_path):
        return _detect_from_imu(imu_path, fps, total_frames)
    else:
        print("No hay IMU, usando video...")
        return _detect_from_video(video_path, fps)


def _detect_from_imu(imu_path, fps, total_frames):
    """
    Columnas asumidas: [timestamp, ax, ay, az, gx, gy, gz, qw, qx, qy, qz]
    Idle del operador = magnitud del giroscopio (cols 4-6) cerca de cero.
    """
    data = np.load(imu_path, allow_pickle=True)
    print(f"IMU: {data.shape[0]} filas × {data.shape[1]} columnas")

    # Magnitud del giroscopio
    gyro = data[:, 4:7]
    gyro_mag = np.sqrt((gyro ** 2).sum(axis=1))

    # Suavizar con ventana de 3 segundos (3*fps muestras)
    window = max(1, int(3 * fps))
    gyro_smooth = uniform_filter1d(gyro_mag, size=window)

    # Tiempo en segundos para cada muestra
    n = len(gyro_smooth)
    times = np.arange(n) / fps

    # Umbral adaptativo: operador inactivo = por debajo del percentil 30
    threshold = np.percentile(gyro_smooth, 30)
    print(f"Gyro stats: mean={gyro_smooth.mean():.3f}, p30={threshold:.3f}, max={gyro_smooth.max():.3f}")

    # Detectar ventanas de baja actividad
    is_idle = gyro_smooth < threshold
    truck_events = []
    in_idle = False
    t_start = 0

    for i, (t, idle) in enumerate(zip(times, is_idle)):
        if idle and not in_idle:
            in_idle = True
            t_start = t
        elif not idle and in_idle:
            in_idle = False
            duration = t - t_start
            if duration >= 20:  # intercambio real dura > 20s
                truck_events.append({
                    "t_arrival": float(t_start),
                    "t_departure": float(t),
                    "exchange_duration_s": float(duration)
                })
                print(f"[{t_start:05.1f}s - {t:05.1f}s] Intercambio detectado ({duration:.1f}s)")

    # Si el video termina en idle
    if in_idle:
        t = times[-1]
        duration = t - t_start
        if duration >= 20:
            truck_events.append({
                "t_arrival": float(t_start),
                "t_departure": float(t),
                "exchange_duration_s": float(duration)
            })

    _save(truck_events, gyro_smooth, times)
    return truck_events


def _detect_from_video(video_path, fps):
    """Fallback: frame-to-frame diff suavizado."""
    cap = cv2.VideoCapture(video_path)
    ret, primer_frame = cap.read()
    if not ret:
        return []

    x, y, w, h = 5, 183, 682, 229
    fh, fw = primer_frame.shape[:2]
    x1, y1, x2, y2 = x, y, (x+w if w else fw), (y+h if h else fh)

    kernel = np.ones((5, 5), np.uint8)
    prev_gray = cv2.cvtColor(primer_frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    sample_n = max(1, int(fps))
    scores, times = [], []
    frame_count = 1

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % sample_n == 0:
            gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(gray, prev_gray)
            _, db = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            db = cv2.morphologyEx(db, cv2.MORPH_OPEN, kernel)
            scores.append(np.sum(db > 0) / db.size)
            times.append(frame_count / fps)
            prev_gray = gray
        frame_count += 1
    cap.release()

    if not scores:
        return []

    scores_arr = np.array(scores)
    times_arr = np.array(times)
    # Suavizar con ventana de 15s
    smoothed = uniform_filter1d(scores_arr, size=15)
    threshold = smoothed.mean() + smoothed.std()

    is_high = smoothed > threshold
    truck_events = []
    in_event, t_start = False, 0

    for t, high in zip(times_arr, is_high):
        if high and not in_event:
            in_event, t_start = True, t
        elif not high and in_event:
            in_event = False
            duration = t - t_start
            if duration >= 10:
                truck_events.append({
                    "t_arrival": float(t_start),
                    "t_departure": float(t),
                    "exchange_duration_s": float(duration)
                })
                print(f"[{t_start:.1f}s - {t:.1f}s] Intercambio video ({duration:.1f}s)")

    _save(truck_events, smoothed, times_arr)
    return truck_events


def _save(events, signal, times):
    os.makedirs('./outputs', exist_ok=True)
    with open('./outputs/truck_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    debug = [{"t": float(t), "signal": float(s)} for t, s in zip(times, signal)]
    with open('./outputs/motion_debug.json', 'w') as f:
        json.dump(debug, f, indent=2)
    print(f"\nPIPELINE COMPLETADO. {len(events)} intercambios → outputs/truck_events.json")


if __name__ == '__main__':
    detect_truck_events(
        video_path="./inputs/40343737_20260313_110600_to_112100_left.mp4",
        imu_path="./inputs/40343737_20260313_110600_to_112100_imu.npy"
    )
