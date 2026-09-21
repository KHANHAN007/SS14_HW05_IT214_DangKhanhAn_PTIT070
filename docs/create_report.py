from pathlib import Path
import sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def register_fonts():
    root = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("ArialVN", str(root / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("ArialVN-Bold", str(root / "Arial Bold.ttf")))


def build_report(student_name, student_id, output_path):
    register_fonts()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("ArialVN", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(20 * mm, 12 * mm, "SS14 HW05 - Orchestration Saga đặt combo")
        canvas.drawRightString(190 * mm, 12 * mm, f"Trang {doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                          topMargin=18*mm, bottomMargin=20*mm,
                          title="SS14 HW05 - Hệ thống đặt vé combo", author=student_name)
    doc.addPageTemplates(PageTemplate(id="main", frames=Frame(doc.leftMargin, doc.bottomMargin,
                         doc.width, doc.height, id="frame"), onPage=footer))
    base = getSampleStyleSheet()
    title = ParagraphStyle("TitleVN", parent=base["Title"], fontName="ArialVN-Bold",
                           fontSize=19, leading=24, alignment=TA_CENTER,
                           textColor=colors.HexColor("#123047"), spaceAfter=9)
    sub = ParagraphStyle("Sub", parent=base["Normal"], fontName="ArialVN", fontSize=10.5,
                         leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#52606d"), spaceAfter=16)
    h1 = ParagraphStyle("H1", parent=base["Heading1"], fontName="ArialVN-Bold", fontSize=14,
                        leading=18, textColor=colors.HexColor("#075985"), spaceBefore=7, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=base["Heading2"], fontName="ArialVN-Bold", fontSize=11.3,
                        leading=15, textColor=colors.HexColor("#0f766e"), spaceBefore=5, spaceAfter=4)
    body = ParagraphStyle("Body", parent=base["BodyText"], fontName="ArialVN", fontSize=10,
                          leading=14.5, textColor=colors.HexColor("#1f2937"), spaceAfter=5)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, firstLineIndent=-7, bulletIndent=3, spaceAfter=3)
    box = ParagraphStyle("Box", parent=body, borderColor=colors.HexColor("#7dd3fc"), borderWidth=.7,
                         borderPadding=8, backColor=colors.HexColor("#f0f9ff"), spaceBefore=5, spaceAfter=8)

    def table(rows, widths):
        header = ParagraphStyle("TableHeader", parent=body, fontName="ArialVN-Bold", textColor=colors.white)
        wrapped = [[Paragraph(str(cell), header if index == 0 else body) for cell in row]
                   for index, row in enumerate(rows)]
        t = Table(wrapped, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#075985")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "ArialVN-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ("GRID", (0,0), (-1,-1), .5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        return t

    story = [
        Paragraph("HỒ SƠ THIẾT KẾ KIẾN TRÚC", title),
        Paragraph("Hệ thống đặt combo Chuyến đi trọn gói", title),
        Paragraph(f"Sinh viên: <b>{student_name}</b> | Lớp: <b>IT214</b> | Mã sinh viên: <b>{student_id}</b>", sub),
        Paragraph("1. Phân tích bài toán", h1),
        Paragraph("Giao dịch gồm giữ vé máy bay, giữ phòng khách sạn và thanh toán. Mỗi bước thuộc một hệ thống độc lập nên không thể khóa chung dữ liệu hoặc rollback bằng một transaction ACID. Mục tiêu là đạt tính nhất quán cuối: hoặc mọi bước cùng thành công, hoặc những bước đã hoàn tất được bù trừ.", body),
        Paragraph("• Combo Orchestrator: nhận yêu cầu, lưu tiến độ Saga và quyết định bù trừ.", bullet),
        Paragraph("• Flight Service: giữ vé; hành động bù trừ là hủy giữ vé.", bullet),
        Paragraph("• Hotel Service: giữ phòng; hành động bù trừ là hủy giữ phòng.", bullet),
        Paragraph("• Payment Service: thu tiền; hành động bù trừ là hoàn tiền.", bullet),
        Paragraph("Đầu vào: customerId, flightCode, hotelCode, amount. Đầu ra: mã combo, trạng thái cuối, mã đặt chỗ và thông báo.", box),
        Paragraph("2. Lựa chọn mô hình", h1),
        Paragraph("Bài chọn Orchestration Saga. Hai đối tác có API, timeout và mã lỗi khác nhau; trình tự giữ vé - giữ phòng - thanh toán cũng rất rõ. Một orchestrator giúp quan sát trạng thái tại một nơi và gọi compensate theo thứ tự ngược. Choreography giảm phụ thuộc trung tâm nhưng sẽ tạo nhiều event và khó xác định bước đang lỗi khi số nhánh tăng.", body),
        Paragraph("3. Điểm có thể thất bại", h1),
        table([
            ["Bước", "Rủi ro", "Cách xử lý"],
            ["Giữ vé", "Hết chỗ, lỗi mạng", "Dừng Saga, hủy combo"],
            ["Giữ phòng", "Hết phòng, timeout", "Hủy vé đã giữ"],
            ["Thanh toán", "Bị từ chối, timeout", "Hủy phòng rồi hủy vé"],
            ["Xác nhận cuối", "Orchestrator lỗi", "Hoàn tiền, hủy phòng, hủy vé"],
            ["Compensate", "Đối tác tạm lỗi", "Retry riêng và ghi trạng thái cần xử lý"],
        ], [31*mm, 57*mm, 79*mm]),
        PageBreak(),
        Paragraph("4. Sơ đồ kiến trúc và luồng", h1),
        Paragraph("Khách hàng → Combo Orchestrator → Flight API → Hotel API → Payment API", box),
        Paragraph("Luồng thành công", h2),
        Paragraph("1. Tạo combo PENDING. 2. Giữ vé. 3. Giữ phòng. 4. Thanh toán. 5. Chuyển combo sang CONFIRMED.", body),
        Paragraph("PENDING → FLIGHT_RESERVED → HOTEL_RESERVED → PAID → CONFIRMED", box),
        Paragraph("Luồng bù trừ", h2),
        table([
            ["Kịch bản", "Các bước đã thành công", "Bù trừ theo thứ tự ngược"],
            ["Hotel thất bại", "Flight", "Cancel Flight → CANCELLED"],
            ["Hotel timeout", "Flight", "Hết retry → Cancel Flight → CANCELLED"],
            ["Payment thất bại", "Flight, Hotel", "Cancel Hotel → Cancel Flight → CANCELLED"],
            ["Lỗi sau Payment", "Flight, Hotel, Payment", "Refund → Cancel Hotel → Cancel Flight"],
        ], [38*mm, 51*mm, 78*mm]),
        Spacer(1, 8),
        Paragraph("5. Timeout, retry và idempotency", h1),
        Paragraph("Hotel API có timeout 2 giây. Lỗi mạng hoặc 5xx được retry tối đa 2 lần, cách nhau 500 ms. Lỗi nghiệp vụ HTTP 422 không retry vì thử lại ngay không thay đổi kết quả. Sau khi hết retry, orchestrator chạy compensate.", body),
        Paragraph("Các API cancel và refund phải idempotent theo reservationId/paymentId. Gọi lặp lại vẫn trả trạng thái CANCELLED hoặc REFUNDED, không thực hiện nghiệp vụ hai lần. Trong production, Saga state và idempotency key phải lưu bền vững thay vì chỉ dùng RAM.", body),
        Paragraph("6. Cấu trúc source demo", h1),
        Paragraph("• combo-orchestrator (8080): WebClient, SagaContext, timeout, retry và compensate.", bullet),
        Paragraph("• flight-service (8081): reserve/cancel vé.", bullet),
        Paragraph("• hotel-service (8082): reserve/cancel phòng, giả lập lỗi và chậm 5 giây.", bullet),
        Paragraph("• payment-service (8083): charge/refund.", bullet),
        PageBreak(),
        Paragraph("7. Kịch bản nghiệm thu", h1),
        table([
            ["Scenario", "Kết quả mong đợi"],
            ["SUCCESS", "Vé, phòng và thanh toán thành công; combo CONFIRMED."],
            ["HOTEL_FAIL", "Flight đã giữ được hủy; combo CANCELLED."],
            ["PAYMENT_FAIL", "Hotel và Flight được hủy; combo CANCELLED."],
            ["HOTEL_TIMEOUT", "Hotel vượt timeout, hết retry, Flight được hủy."],
        ], [43*mm, 124*mm]),
        Paragraph("8. Đánh đổi và hướng production", h1),
        Paragraph("Orchestration dễ debug và kiểm soát bù trừ, nhưng orchestrator có thể thành nút nghẽn. Cần triển khai nhiều instance, lưu trạng thái Saga bền vững, dùng transactional outbox/message broker, correlationId và distributed tracing. Lệnh compensate thất bại phải được đưa vào hàng đợi retry hoặc DLQ để nhân viên vận hành xử lý.", body),
        Paragraph("Không nên retry mù quáng thao tác thanh toán. Mọi request tới đối tác cần idempotency key để tránh trừ tiền hoặc đặt chỗ hai lần khi phản hồi trước bị thất lạc.", body),
        Paragraph("9. Kết luận", h1),
        Paragraph("Saga không tạo tính nguyên tử tức thời như transaction cơ sở dữ liệu, nhưng cung cấp tính nhất quán cuối bằng các giao dịch cục bộ và hành động bù trừ. Với combo có trình tự cố định và nhiều API đối tác, Orchestration là lựa chọn dễ hiểu, dễ kiểm thử và phù hợp nhất cho bản thiết kế này.", body),
    ]
    doc.build(story)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: create_report.py <student_name> <student_id> <output_pdf>")
    build_report(sys.argv[1], sys.argv[2], sys.argv[3])
