from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "architecture.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str) -> None:
    title_font = font(22, bold=True)
    body_font = font(16)
    lines = text.split("\n")
    heights = []
    widths = []
    for index, line in enumerate(lines):
        selected = title_font if index == 0 else body_font
        bbox = draw.textbbox((0, 0), line, font=selected)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_height = sum(heights) + (len(lines) - 1) * 8
    y = box[1] + ((box[3] - box[1]) - total_height) / 2
    for index, line in enumerate(lines):
        selected = title_font if index == 0 else body_font
        x = box[0] + ((box[2] - box[0]) - widths[index]) / 2
        draw.text((x, y), line, fill="#1f2933", font=selected)
        y += heights[index] + 8


def draw_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fill: str) -> None:
    draw.rounded_rectangle(box, radius=16, fill=fill, outline="#2f4050", width=2)
    draw_centered_text(draw, box, text)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line((start, end), fill="#465a69", width=4)
    x1, y1 = start
    x2, y2 = end
    if x2 > x1:
        points = [(x2, y2), (x2 - 14, y2 - 8), (x2 - 14, y2 + 8)]
    elif x2 < x1:
        points = [(x2, y2), (x2 + 14, y2 - 8), (x2 + 14, y2 + 8)]
    else:
        points = [(x2, y2), (x2 - 8, y2 - 14), (x2 + 8, y2 - 14)]
    draw.polygon(points, fill="#465a69")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1800, 1050), "#eef2f6")
    draw = ImageDraw.Draw(image)

    draw.text((60, 40), "IBM Intelligent Incident Categorization & Knowledge Search", fill="#1f2933", font=font(34, True))
    draw.text((62, 88), "End-to-end enterprise NLP architecture", fill="#607080", font=font(20))

    boxes = [
        ((70, 180, 350, 300), "Ticket\nServiceNow / ITSM", "#d0e2ff"),
        ((430, 180, 710, 300), "Spring Boot API\nRequest validation", "#e5f6ff"),
        ((790, 180, 1070, 300), "Kafka\nincident-events", "#fff1c7"),
        ((1150, 180, 1430, 300), "Python FastAPI\nNLP inference", "#defbe6"),
        ((790, 420, 1070, 540), "BERT Classifier\ncategory + confidence", "#ffd7d9"),
        ((1150, 420, 1430, 540), "SBERT Embeddings\nsemantic vector", "#e8daff"),
        ((790, 660, 1070, 780), "Vector Search\ncosine similarity", "#bae6ff"),
        ((1150, 660, 1430, 780), "Knowledge Base\narticles + runbooks", "#fddc69"),
        ((430, 660, 710, 780), "Redis Cache\nrecent results", "#ffd6a5"),
        ((70, 660, 350, 780), "Frontend Dashboard\ntriage workbench", "#d9fbfb"),
    ]

    for box, label, color in boxes:
        draw_box(draw, box, label, color)

    draw_arrow(draw, (350, 240), (430, 240))
    draw_arrow(draw, (710, 240), (790, 240))
    draw_arrow(draw, (1070, 240), (1150, 240))
    draw_arrow(draw, (1290, 300), (930, 420))
    draw_arrow(draw, (1290, 300), (1290, 420))
    draw_arrow(draw, (1290, 540), (930, 660))
    draw_arrow(draw, (1070, 720), (1150, 720))
    draw_arrow(draw, (790, 720), (710, 720))
    draw_arrow(draw, (430, 720), (350, 720))

    footer = "Deployment: Docker images on Kubernetes / OpenShift | CI/CD: Jenkins build, test, push, deploy"
    draw.rounded_rectangle((70, 880, 1730, 960), radius=16, fill="#ffffff", outline="#d6dde5", width=2)
    draw.text((105, 908), footer, fill="#1f2933", font=font(22, True))

    image.save(OUTPUT)


if __name__ == "__main__":
    main()
