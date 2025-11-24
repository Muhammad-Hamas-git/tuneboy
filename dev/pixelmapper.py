import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageDraw # Import Pillow modules

GRID_SIZE = 16
CELL_SIZE = 20

BG_COLOR = "#000000"       # black
PIXEL_ON = "#00FF00"       # green
PIXEL_OFF = "#000000"      # black

class PixelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("TuneBoy Pixel Editor")

        self.canvas = tk.Canvas(
            root,
            width=GRID_SIZE * CELL_SIZE,
            height=GRID_SIZE * CELL_SIZE,
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack()

        self.grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.rects = [[None]*GRID_SIZE for _ in range(GRID_SIZE)]

        self.draw_grid()

        # mouse bindings
        self.canvas.bind("<Button-1>", self.fill_cell)
        self.canvas.bind("<B1-Motion>", self.fill_cell)
        self.canvas.bind("<Button-3>", self.clear_cell)
        self.canvas.bind("<B3-Motion>", self.clear_cell)

        # buttons
        btn_frame = tk.Frame(root, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Export Binary", command=self.export_binary).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Import Binary", command=self.import_binary).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export Image (PNG)", command=self.export_image).pack(side="left", padx=5)
        # New ICO Export Button
        tk.Button(btn_frame, text="Export Icon (ICO)", command=self.export_ico).pack(side="left", padx=5)

    def draw_grid(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#003300",
                    fill=PIXEL_OFF
                )
                self.rects[r][c] = rect

    def get_cell(self, event):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None, None

    def fill_cell(self, event):
        row, col = self.get_cell(event)
        if row is None: return
        self.grid[row][col] = 1
        self.canvas.itemconfig(self.rects[row][col], fill=PIXEL_ON)

    def clear_cell(self, event):
        row, col = self.get_cell(event)
        if row is None: return
        self.grid[row][col] = 0
        self.canvas.itemconfig(self.rects[row][col], fill=PIXEL_OFF)

    def export_binary(self):
        bits = "".join(
            str(self.grid[r][c])
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(bits)
        messagebox.showinfo("Exported", "Copied binary string to clipboard!")

    def import_binary(self):
        data = simpledialog.askstring("Import Binary", "Paste 256-bit string:")
        if not data:
            return

        data = data.strip()

        if len(data) != GRID_SIZE * GRID_SIZE or any(ch not in "01" for ch in data):
            messagebox.showerror("Error", "Invalid binary data (must be 256 characters of 0/1).")
            return

        # load into grid
        idx = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = int(data[idx])
                self.grid[r][c] = val
                color = PIXEL_ON if val == 1 else PIXEL_OFF
                self.canvas.itemconfig(self.rects[r][c], fill=color)
                idx += 1

        messagebox.showinfo("Imported", "Binary art loaded successfully!")

    # Helper method to create a single 16x16 Pillow Image
    def create_base_image(self):
        # Create a 16x16 image, not scaled by CELL_SIZE
        image_size = GRID_SIZE
        image = Image.new('RGB', (image_size, image_size), color=BG_COLOR)
        draw = ImageDraw.Draw(image)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                # Coordinates for a 1x1 pixel on the 16x16 image
                x1 = c
                y1 = r
                x2 = c
                y2 = r
                
                color = PIXEL_ON if self.grid[r][c] == 1 else PIXEL_OFF
                
                # Use point/rectangle to draw the 1x1 pixel
                draw.point((x1, y1), fill=color)

        return image

    def export_image(self):
        # This function exports a single large PNG
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Image"
        )
        if not filename:
            return

        # Create the base 16x16 image, then upscale it for a nice-looking PNG
        base_image = self.create_base_image()
        
        # Scale the image up to the size of the canvas for the PNG export
        final_png_size = GRID_SIZE * CELL_SIZE
        upscaled_image = base_image.resize(
            (final_png_size, final_png_size), 
            resample=Image.NEAREST # Use nearest neighbor for crisp pixel art scaling
        )

        try:
            upscaled_image.save(filename)
            messagebox.showinfo("Export Successful", f"PNG Image saved as {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save image: {e}")

    def export_ico(self):
        # 1. Ask user for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".ico",
            filetypes=[("Icon files", "*.ico")],
            title="Save Icon File"
        )
        if not filename:
            return # User cancelled

        # 2. Get the base 16x16 image
        base_image = self.create_base_image()

        # 3. Define the sizes to include in the ICO file
        # Windows typically uses 16, 32, and 48 (or 64, 256) for scaling.
        # We will use 16, 32, and 64 for good modern support.
        ico_sizes = [(16, 16), (32, 32), (64, 64)]

        # 4. Save the image to the ICO format with multiple sizes
        # Pillow handles the necessary resizing and packaging into the ICO container.
        try:
            base_image.save(
                filename, 
                format='ICO', 
                sizes=ico_sizes # This list tells Pillow which resolutions to include
            )
            messagebox.showinfo("Export Successful", f"Icon (.ico) saved as {filename} with sizes {', '.join([str(s[0])+'x'+str(s[1]) for s in ico_sizes])}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save ICO: {e}\n(Ensure your Pillow version supports ICO with multiple sizes.)")


if __name__ == "__main__":
    root = tk.Tk()
    PixelEditor(root)
    root.configure(bg=BG_COLOR)
    root.mainloop()