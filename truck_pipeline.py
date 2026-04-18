import cv2
import numpy as np
import json
import os

def detect_truck_events(video_path, output_dir='./outputs'):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # Analizamos 1 frame cada 1 segundo para ser ultra rápidos pero precisos
    sample_every_n = int(fps) 
    
    # ─── CONFIGURA TUS COORDENADAS AQUÍ ───
    # Reemplaza estos números con lo que viste en Vista Previa
    x, y, w, h = 5, 183, 682, 229  # <--- CAMBIA ESTO
    
    x1, y1 = x, y
    x2, y2 = x + w, y + h
    
    bg_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    
    truck_events = []
    camion_presente = False
    t_arrival = 0
    frame_count = 0

    print(f"Procesando {video_path}...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % sample_every_n == 0:
            t_actual = frame_count / fps
            
            # Recortar zona del camión
            roi = frame[y1:y2, x1:x2]
            
            # Aplicar sustracción de fondo
            mask = bg_sub.apply(roi)
            
            # Limpiar ruido
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Calcular porcentaje de ocupación
            occupancy = np.sum(mask > 0) / mask.size
            
            # Lógica de detección (Umbral 30%)
            is_truck_here = occupancy > 0.3
            
            if is_truck_here and not camion_presente:
                camion_presente = True
                t_arrival = t_actual
                print(f"Camión detectado en t={t_actual:.1f}s")
            elif not is_truck_here and camion_presente:
                camion_presente = False
                duration = t_actual - t_arrival
                if duration > 5: # Ignorar falsos positivos rápidos
                    truck_events.append({
                        "t_arrival": float(t_arrival),
                        "t_departure": float(t_actual),
                        "duration_s": float(duration)
                    })
                    print(f"Camión se retiró en t={t_actual:.1f}s")
                
        frame_count += 1
        
    cap.release()
    return truck_events

if __name__ == '__main__':
    # Prueba local rápida
    video = "./inputs/40343737_20260313_110600_to_112100_left.mp4"
    if os.path.exists(video):
        events = detect_truck_events(video)
        with open('./outputs/truck_events.json', 'w') as f:
            json.dump(events, f, indent=2)