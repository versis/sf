from enum import Enum

class QrCodeMode(str, Enum):
    NO_QR_CODE = "no_qr_code"
    MAIN_PAGE = "main_page"
    CARD_PAGE = "card_page" 