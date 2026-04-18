import cv2

# Carga la imagen donde sale el camión en el minuto 2:06
# Si guardaste la captura de pantalla con otro nombre, cámbialo aquí
img = cv2.imread("roi_test2.jpg") 

if img is None:
    print("Error: No se encontró la imagen. Asegúrate de poner el nombre correcto.")
else:
    # Abre una ventana interactiva
    roi = cv2.selectROI("Selecciona el camion y presiona ENTER o ESPACIO", img)
    cv2.destroyAllWindows()
    
    print("\n" + "="*40)
    print(f"¡LISTO! COPIA ESTO EN TU truck_pipeline.py:")
    print(f"x, y, w, h = {roi[0]}, {roi[1]}, {roi[2]}, {roi[3]}")
    print("="*40 + "\n")