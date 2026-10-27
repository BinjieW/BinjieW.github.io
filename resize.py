from pathlib import Path
from PIL import Image

# 原图路径
img_path = Path("assets/img/publication_preview/factool.png")

# 读入原图
img = Image.open(img_path)

# 想要的新宽度（可以改成 600 / 500 / 400 等）
new_width = 1200

# 等比例缩小
w, h = img.size
# import pdb; pdb.set_trace()
new_height = int(h * new_width / w)

# 缩放
img_resized = img.resize((new_width, new_height), Image.LANCZOS)

# 建议先保存为新文件，确认效果后再替换原图
out_path = Path("assets/img/publication_preview/factool_small.png")
img_resized.save(out_path)

print("done:", out_path, "size:", img_resized.size)