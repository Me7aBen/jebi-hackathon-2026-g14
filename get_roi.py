import cv2

def extract_first_frame(video_path, output_image="roi_test2.jpg"):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 126000)

    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_image, frame)
        print(f"Frame guardado exitosamente como {output_image}")
        print(f"Resolución de la imagen: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("Error al leer el video.")
    cap.release()

if __name__ == '__main__':
    # Asegúrate de que la ruta apunte correctamente a tu archivo izquierdo
    extract_first_frame("./inputs/40343737_20260313_110600_to_112100_left.mp4")