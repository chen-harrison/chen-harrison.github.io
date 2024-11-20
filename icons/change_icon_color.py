import cv2
import numpy as np
import os

hex_color = '#51c660'

def hexToRGB(hex: str):
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4))

if __name__ == '__main__':
    rgb = hexToRGB(hex_color)

    icon_dir = os.path.dirname(os.path.realpath(__file__))
    icon_files = [name for name in os.listdir(icon_dir) if '.png' in name]
    
    for icon_file in icon_files:
        icon_path = os.path.join(icon_dir, icon_file)
        img = cv2.imread(icon_path, cv2.IMREAD_UNCHANGED)

        for x in range(img.shape[0]):
            for y in range(img.shape[1]):
                # If not transparent, turn RGB into desired color
                if img[x, y, 3] != 0:
                    img[x, y, :3] = np.array([rgb[0], rgb[1], rgb[2]])
                else:
                    img[x, y, :3] = np.array([255, 255, 255])
        
        cv2.imwrite(icon_path, img)
