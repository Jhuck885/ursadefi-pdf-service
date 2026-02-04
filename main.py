from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import qrcode
import io
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "UrsaDeFi PDF service LIVE with CORS"}

class InvoiceData(BaseModel):
    invoice_id: str
    client_name: str
    amount: float
    currency: str = "XRP"
    description: str = ""
    due_date: str = ""
    memo: str = ""
    to_wallet: str

@app.post("/generate-pdf")
async def generate_pdf(data: InvoiceData):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 60, "UrsaDeFi Invoice")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Invoice #: {data.invoice_id}")
    p.drawString(50, height - 120, f"Client: {data.client_name}")
    p.drawString(50, height - 140, f"Amount: {data.amount} {data.currency}")
    p.drawString(50, height - 160, f"Description: {data.description}")
    p.drawString(50, height - 180, f"Due Date: {data.due_date or 'None'}")
    p.drawString(50, height - 200, f"Memo: {data.memo or 'None'}")
    p.drawString(50, height - 220, f"To: {data.to_wallet[:8]}...{data.to_wallet[-4:]}")

    payment_uri = f"xrp:{data.to_wallet}?amount={data.amount}&dt={data.invoice_id}"
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(payment_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_path = f"/tmp/qr_{data.invoice_id}.png"
 scatter img.save(img_path)

    p.drawImage(img_path, 400, height - 280, width=100, height=100)
    p.setFont("Helvetica", 10)
    p.drawString(400, height - 300, "Scan to Pay")

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{data.invoice_id}.pdf"}
    )
