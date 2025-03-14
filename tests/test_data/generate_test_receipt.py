from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def create_test_receipt():
    # Create a new image with white background
    width = 400
    height = 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a basic font
    try:
        font = ImageFont.truetype("Arial", 16)
    except:
        font = ImageFont.load_default()

    # Receipt content
    receipt_text = [
        "AMAZON.COM",
        "-----------------------",
        f"Order Date: {datetime.now().strftime('%Y-%m-%d')}",
        "Order #: 123-456-789",
        "-----------------------",
        "Items:",
        "1x Ceramic Coffee Mug",
        "    $24.99",
        "-----------------------",
        "Subtotal:     $24.99",
        "Tax:           $2.00",
        "Total:        $26.99",
        "-----------------------",
        "Payment Method:",
        "VISA ***1234",
        "-----------------------",
        "Thank you for shopping",
        "at Amazon.com!"
    ]

    # Draw text
    y_position = 50
    for line in receipt_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30

    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), "test_receipt.png")
    image.save(output_path)
    return output_path

if __name__ == "__main__":
    receipt_path = create_test_receipt()
    print(f"Test receipt created at: {receipt_path}") 