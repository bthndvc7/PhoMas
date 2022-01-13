import cv2


class Sketcher:
    def __init__(self, username, filename):
        self.filename = filename
        self.username = username

    def sketch(self):
        # Read Image
        img = cv2.imread(f"static/uploaded_imgs/{self.username}/{self.filename}")

        # Convert to Grey Image
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Invert Image
        invert_img = cv2.bitwise_not(grey_img)

        # Blur image
        blur_img = cv2.GaussianBlur(invert_img, (7, 7), 0)

        # Invert Blurred Image
        invblur_img = cv2.bitwise_not(blur_img)

        # Sketch Image
        sketch_img = cv2.divide(grey_img, invblur_img, scale=256.0)

        # Save Sketch
        cv2.imwrite(f'static/imgs_out/{self.username}/sketched_{self.filename}', sketch_img)

