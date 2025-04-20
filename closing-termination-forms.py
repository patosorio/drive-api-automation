import os
import tempfile

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas  # type: ignore


def adjust_coordinates(
        x: int,
        y: int,
        page_height: float) -> tuple[int, float]:
    """
    Adjust Y-coordinate for ReportLab.

    Args:
        x: X-coordinate.
        y: Y-coordinate.
        page_height: Height of the PDF page.

    Returns:
        Adjusted coordinates as a tuple (x, y).
    """
    adjusted_y = page_height - y
    return x, adjusted_y


def download_images(
        service,
        passport_selfie_id: str,
        passport_id: str,
        temp_dir: str,
) -> tuple[str, str]:
    """
    Download the passport selfie and passport image from Google Drive.

    Args:
        service: Google Drive API service instance.
        passport_selfie_id: File ID of the passport selfie.
        passport_id: File ID of the passport.
        temp_dir: Path to the temporary directory.

    Returns:
        Tuple containing the file paths of the downloaded
        passport selfie and passport image.
    """

    file_ids = {
        'passport_selfie': passport_selfie_id,
        'passport': passport_id,
    }

    downloaded_paths = {}

    for file_name, file_id in file_ids.items():
        file_path = os.path.join(temp_dir, f'{file_name}.jpg')

        try:
            request = service.files().get_media(fileId=file_id)

            with open(file_path, 'wb') as img_file:
                downloader = MediaIoBaseDownload(img_file, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                downloaded_paths[file_name] = file_path
            else:
                raise ValueError(
                    f'Failed to download file ID {file_id}: '
                    'File is missing or empty.',
                )

        except Exception as e:
            raise RuntimeError(f'Failed to download file ID {file_id}') from e

    return downloaded_paths['passport_selfie'], downloaded_paths['passport']


def fill_application_form(
    data: dict[str, str],
    template_pdf: str,
    output_pdf: str,
    form_type: str,
) -> None:
    """
    Fill the application form with the provided data
    and save the filled PDF.

    Args:
        data: Dictionary containing form field data.
        template_pdf: Path to the template PDF.
        output_pdf: Path to save the filled PDF.
        form_type: Type of form ("closing_account" or "card_termination").
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        overlay_pdf_path = os.path.join(temp_dir, 'temp_overlay.pdf')
        template_reader = PdfReader(template_pdf)
        page_height = float(template_reader.pages[0].mediabox[3])

        c = canvas.Canvas(overlay_pdf_path)
        c.setFont('Helvetica', 9)

        if form_type == 'closing_account':
            c.drawString(
                *adjust_coordinates(149, 210, page_height),
                data.get('account_name', '').upper())
            c.drawString(
                *adjust_coordinates(192, 295, page_height),
                data.get('account_number', '').upper())
            c.drawString(
                *adjust_coordinates(192, 318, page_height),
                data.get('account_name', '').upper())
            c.drawString(
                *adjust_coordinates(273, 346, page_height),
                data.get('balance', '').upper())
            c.drawString(
                *adjust_coordinates(164, 386, page_height),
                data.get('check_number', '').upper())
            c.drawString(
                *adjust_coordinates(409, 404, page_height),
                data.get('unused_check_from', '').upper())
            c.drawString(
                *adjust_coordinates(486, 404, page_height),
                data.get('unused_check_to', '').upper())
            c.drawString(
                *adjust_coordinates(116, 424, page_height),
                data.get('balance', '').upper())
            c.drawString(
                *adjust_coordinates(392, 538, page_height),
                data.get('account_name', '').upper())

        elif form_type == 'card_termination':
            c.drawString(
                *adjust_coordinates(267, 260, page_height),
                data.get('cardholder_name', '').upper())
            c.drawString(
                *adjust_coordinates(211, 274, page_height),
                data.get('current_address', '').upper())
            c.drawString(
                *adjust_coordinates(307, 290, page_height),
                data.get('passport_number', '').upper())
            c.drawString(
                *adjust_coordinates(479, 290, page_height),
                data.get('date_of_issuance', '').upper())
            c.drawString(
                *adjust_coordinates(206, 306, page_height),
                data.get('contact_number', '').upper())
            c.drawString(
                *adjust_coordinates(172, 324, page_height),
                data.get('card_number', '').upper())
            c.drawString(
                *adjust_coordinates(188, 418, page_height),
                data.get('account_number', '').upper())
            c.drawString(
                *adjust_coordinates(404, 492, page_height),
                data.get('email_address', ''))

        c.save()

        overlay_reader = PdfReader(overlay_pdf_path)
        writer = PdfWriter()

        template_page = template_reader.pages[0]
        overlay_page = overlay_reader.pages[0]

        template_page.merge_page(overlay_page)
        writer.add_page(template_page)

        for page_num in range(1, len(template_reader.pages)):
            writer.add_page(template_reader.pages[page_num])

        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)


def generate_forms(
        data: dict[str, str],
        temp_dir: str,
) -> dict[str, str]:
    """
    Generate both the Closing Account and Card Termination forms.

    Args:
        data: Dictionary containing customer data.
    """
    account_owner = data.get('account_name', '').upper().replace(' ', '_')

    # Define template names and paths
    closing_account_template_name = 'Closing-Bank-Account'
    card_termination_template_name = 'Card-Termination-Form'

    closing_account_template = (
        f'./automate-cancellation-form/templates/'
        f'{closing_account_template_name}.pdf')
    card_termination_template = (
        f'./automate-cancellation-form/templates/'
        f'{card_termination_template_name}.pdf')

    closing_account_output = os.path.join(
        temp_dir, f'{account_owner}-Closing-Bank-Account.pdf',
    )
    card_termination_output = os.path.join(
        temp_dir, f'{account_owner}-Card-Termination-Form.pdf',
    )

    fill_application_form(
        data,
        closing_account_template,
        closing_account_output,
        form_type='closing_account',
    )

    fill_application_form(
        data,
        card_termination_template,
        card_termination_output,
        form_type='card_termination',
    )

    return {
        'closing_account_form': closing_account_output,
        'card_termination_form': card_termination_output,
    }


def add_images_to_pdf(
        pdf_paths: str,
        passport_selfie_img: str,
        passport_img: str,
) -> str:
    """
    Add images to specific pages in the existing termination form PDF

    Args:
        pdf_paths: Path termination form to modify
        images: List of images path to add (in order)
        output_pdf: Path to save the modified PDF.

    Raises:
        ValueError: If images are not compatible with required img format.
    """
    valid_extensions = {'.png', '.jpg', '.bmp'}

    for image_path in [passport_selfie_img, passport_img]:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f'Image file not found: {image_path}')
        _, ext = os.path.splitext(image_path.lower())
        if ext not in valid_extensions:
            raise ValueError(
                f"Unsupported image format '{ext}'. "
                f"Only {', '.join(valid_extensions)} are allowed.",
            )

    reader = PdfReader(pdf_paths)
    writer = PdfWriter()
    image_paths = [passport_selfie_img, passport_img]

    for page_num, page in enumerate(reader.pages):
        if page_num in [1, 2]:
            image_index = page_num - 1
            image_path = image_paths[image_index]

            with tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False,
            ) as temp_pdf:
                c = canvas.Canvas(temp_pdf.name, pagesize=A4)

                with Image.open(image_path) as img:
                    img_width, img_height = img.size

                    # Resize the image to fit the width of the A4
                    scale = A4[0] / img_width
                    img = img.resize(
                        (int(img_width * scale), int(img_height * scale)),
                        Image.Resampling.LANCZOS,
                    )

                    c.drawImage(
                        image_path,
                        0,
                        A4[1] - img.height,
                        width=img.width,
                        height=img.height,
                    )
                    c.save()

                temp_reader = PdfReader(temp_pdf.name)
                page.merge_page(temp_reader.pages[0])

        writer.add_page(page)

    with open(pdf_paths, 'wb') as output_file:
        writer.write(output_file)

    if not os.path.exists(pdf_paths) or os.path.getsize(pdf_paths) == 0:
        raise ValueError(
            'Final PDF was not created correctly. Debug needed.')

    return pdf_paths


def process_final_output(
    service,
    customer_data: dict[str, str],
    passport_selfie_id: str,
    passport_id: str,
) -> str:
    """
    Generate the final PDF with the
    termination form and the passport images.

    Args:
        customer_data: Dictionary containing customer data.
        image_folder: Folder containing the passport images.
        final_pdf_path: Path to save the final combined PDF.

    Returns:
        Path to the temporary file containgin the final form.
    """

    if not passport_selfie_id or not passport_id:
        raise ValueError(
            'Both passport selfie and passport images are required.')

    with tempfile.TemporaryDirectory() as temp_dir:
        generated_forms = generate_forms(customer_data, temp_dir)
        termination_form_path = generated_forms['card_termination_form']

        # Downdload images
        passport_selfie_path, passport_path = download_images(
            service, passport_selfie_id, passport_id, temp_dir,
        )

        add_images_to_pdf(
            termination_form_path,
            passport_selfie_img=passport_selfie_path,
            passport_img=passport_path,
        )

        # Clean up downloaded images
        for image_path in [passport_selfie_path, passport_path]:
            if os.path.exists(image_path):
                os.remove(image_path)

        print(f'\n Final PDFs saved in: {temp_dir}')
        print(f'Contents of final temp directory ({temp_dir}):')
        for file in os.listdir(temp_dir):
            print(f' - {file}')

        return temp_dir


if __name__ == '__main__':
    credentials_path = './automate-cancellation-form/credentials.json'
    creds = Credentials.from_service_account_file(
        credentials_path, scopes=['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=creds)

    customer_data = {
        'account_name': 'Example Name',
        'account_type': 'Saving',
        'account_number': '0XX-XXXX-0X-XXXXXXXX',
        'balance': '0.00 USD',
        'check_number': '',
        'unused_check_from': '',
        'unused_check_to': '',
        'pass_book_returned': '',
        'cardholder_name': 'Example Name',
        'current_address': (
            '000 Example Street, City, State 000000'),
        'passport_number': 'AAXXXXXX',
        'date_of_issuance': 'DD MM YYYY',
        'contact_number': '+0000000000',
        'card_number': '0000 0000 0000 0000',
        'email_address': 'test@test.com',
    }

    drive_file_ids = [
        '[your drive file id here]',
        '[your drive file id here]',
    ]

    passport_selfie_img = drive_file_ids[0]
    passport_img = drive_file_ids[1]

    final_pdf_path = process_final_output(
        service,
        customer_data,
        passport_selfie_img,
        passport_img,
    )
