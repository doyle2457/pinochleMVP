from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SCALE = 4
SIZE = (100, 142)
CANVAS = tuple(value * SCALE for value in SIZE)
OUT = Path(__file__).resolve().parents[1] / "images" / "cards_new"
RANKS = ("A", "K", "Q", "J", "10", "9")
SUITS = {
    "clubs": ("♣", "#111111"),
    "diamonds": ("♦", "#c51624"),
    "hearts": ("♥", "#c51624"),
    "spades": ("♠", "#111111"),
}
# Keep all typography within the DejaVu family for straightforward licensing.
RANK_FONT = Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf")
SYMBOL_FONT = Path(r"C:\Windows\Fonts\DejaVuSans.ttf")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size * SCALE)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
             face: ImageFont.FreeTypeFont, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=face)
    draw.text((xy[0] * SCALE - (box[2] - box[0]) / 2 - box[0],
               xy[1] * SCALE - (box[3] - box[1]) / 2 - box[1]),
              text, font=face, fill=fill)


def card_face(rank: str, symbol: str, color: str) -> Image.Image:
    image = Image.new("RGB", CANVAS, "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2 * SCALE, 2 * SCALE, 97 * SCALE, 139 * SCALE),
                           radius=6 * SCALE, outline=color, width=2 * SCALE)

    # Corner indices are intentionally twice the original 15/12 and 13 px sizes.
    corner_rank = font(RANK_FONT, 30 if rank != "10" else 24)
    suit_face = font(SYMBOL_FONT, 26)
    center_face = font(RANK_FONT, 44 if rank != "10" else 36)

    centered(draw, (16, 15), rank, corner_rank, color)
    centered(draw, (16, 39), symbol, suit_face, color)
    centered(draw, (50, 71), rank, center_face, color)

    # Draw the opposite index on a transparent layer, then rotate it 180 degrees.
    corner = Image.new("RGBA", (40 * SCALE, 50 * SCALE), (255, 255, 255, 0))
    cdraw = ImageDraw.Draw(corner)
    centered(cdraw, (20, 13), symbol, suit_face, color)
    centered(cdraw, (20, 37), rank, corner_rank, color)
    corner = corner.rotate(180)
    image.paste(corner, (58 * SCALE, 90 * SCALE), corner)
    return image


def card_back(color: str) -> Image.Image:
    image = Image.new("RGB", CANVAS, "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2 * SCALE, 2 * SCALE, 97 * SCALE, 139 * SCALE),
                           radius=6 * SCALE, outline=color, width=2 * SCALE)
    # Clip a very large 45-degree hatch to the inset card panel.
    mask = Image.new("L", CANVAS, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((6 * SCALE, 6 * SCALE, 93 * SCALE, 135 * SCALE),
                            radius=3 * SCALE, fill=255)
    hatch = Image.new("RGB", CANVAS, "white")
    hdraw = ImageDraw.Draw(hatch)
    spacing = 22 * SCALE
    width = 10 * SCALE
    for offset in range(-CANVAS[1], CANVAS[0] + CANVAS[1], spacing):
        hdraw.line((offset, CANVAS[1], offset + CANVAS[1], 0), fill=color, width=width)
    image.paste(hatch, (0, 0), mask)
    return image


def save(image: Image.Image, name: str) -> None:
    final = image.resize(SIZE, Image.Resampling.LANCZOS)
    final.save(OUT / name, format="PNG", optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for suit, (symbol, color) in SUITS.items():
        for rank in RANKS:
            save(card_face(rank, symbol, color), f"{suit}_{rank}.png")
    save(card_back("#c51624"), "back_Red.png")
    save(card_back("#111111"), "back_Black.png")


if __name__ == "__main__":
    main()
