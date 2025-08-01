from flask import Flask, render_template, request, send_file, redirect, url_for
import pdfkit
import os
from datetime import datetime, timedelta
import pandas as pd

CSV_FILE = "consulting_quotes_history.csv"

# ✅ 견적 이력 저장 함수
def save_quote_history(company, doc_number, total_price):
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
        else:
            df = pd.DataFrame(columns=["문서번호", "생성일시", "회사명", "견적합계", "수임여부"])

        new_record = {
            "문서번호": f"HYQ-{doc_number}",
            "생성일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "회사명": company,
            "견적합계": total_price,
            "수임여부": "미수임"
        }

        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        print(f"✅ 견적 이력 저장 완료: {CSV_FILE}")
    except Exception as e:
        print("❌ 견적 이력 저장 중 오류:", e)

# ✅ wkhtmltopdf 경로 지정 (Windows 경로 예시)
config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    company = request.form.get('company')
    doc_number_suffix = request.form.get('doc_number')
    total_cost = request.form.get("totalCost")

    selected_services = request.form.getlist('service')
    prices = request.form.getlist('price')

    services = []
    total = 0
    for service, price in zip(selected_services, prices):
        price_value = int(price) if price.isdigit() else 0
        services.append({'name': service, 'price': price_value})
        total += price_value

    now = datetime.now()
    vat_total = int(total * 1.1)
    year_suffix = now.strftime('%y')
    full_doc_number = f"HYQ-{year_suffix}{doc_number_suffix}"

    return render_template(
        'preview.html',
        company=company,
        services=services,
        total=total,
        vat_total=vat_total,
        now=now,
        timedelta=timedelta,
        doc_number=full_doc_number
    )

@app.route('/download', methods=['POST'])
def download():
    company = request.form.get('company')
    doc_number_suffix = request.form.get('doc_number')
    selected_services = request.form.getlist('service')
    prices = request.form.getlist('price')

    services = []
    total = 0
    for service, price in zip(selected_services, prices):
        price_value = int(price) if price.isdigit() else 0
        services.append({'name': service, 'price': price_value})
        total += price_value

    now = datetime.now()
    vat_total = int(total * 1.1)
    year_suffix = now.strftime('%y')
    full_doc_number = f"{year_suffix}{doc_number_suffix}"

    rendered = render_template(
        'quote.html',
        company=company,
        doc_number=doc_number_suffix,
        services=services,
        total=total,
        vat_total=vat_total,
        now=now,
        timedelta=timedelta
    )

    date_str = now.strftime('%y%m%d')
    sanitized_company = company.replace(" ", "").replace("/", "-")
    filename = f"[관세법인한영] {sanitized_company} 과세자료 컨설팅 견적서_{date_str}.pdf"
    output_path = os.path.join(os.getcwd(), filename)

    # PDF 생성
    pdfkit.from_string(rendered, output_path, configuration=config)

    # 견적 이력 저장
    save_quote_history(company, full_doc_number, vat_total)

    
    # PDF 다운로드
    return send_file(output_path, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/history')
def history():
    filename = request.args.get('filename')
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)

        # 견적합계 정수로 변환 및 포맷
        df['견적합계'] = df['견적합계'].apply(lambda x: f"{int(x):,}")
        quotes = df.to_dict(orient='records')
    else:
        quotes = []

    return render_template('history.html', quotes=quotes, filename=filename)


if __name__ == '__main__':
    app.run(debug=True)
