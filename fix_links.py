import re

# Исправляем reports-frontend/index1.html
with open('reports-frontend/index1.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем ссылки на файлы
content = re.sub(r'href=\{report\.bybit_file\}', 'href={"/uploads/" + report.bybit_file}', content)
content = re.sub(r'href=\{report\.htx_file\}', 'href={"/uploads/" + report.htx_file}', content)
content = re.sub(r'href=\{report\.bliss_file\}', 'href={"/uploads/" + report.bliss_file}', content)
content = re.sub(r'src=\{report\.start_photo\}', 'src={"/uploads/" + report.start_photo}', content)
content = re.sub(r'src=\{report\.end_photo\}', 'src={"/uploads/" + report.end_photo}', content)
content = re.sub(r'setZoomedImage\(report\.start_photo\)', 'setZoomedImage("/uploads/" + report.start_photo)', content)
content = re.sub(r'setZoomedImage\(report\.end_photo\)', 'setZoomedImage("/uploads/" + report.end_photo)', content)

with open('reports-frontend/index1.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Исправления применены к reports-frontend/index1.html")

# Исправляем templates/index.html
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content2 = f.read()

# Заменяем ссылки на файлы
content2 = re.sub(r'href=\{report\.bybit_file\}', 'href={"/uploads/" + report.bybit_file}', content2)
content2 = re.sub(r'href=\{report\.htx_file\}', 'href={"/uploads/" + report.htx_file}', content2)
content2 = re.sub(r'href=\{report\.bliss_file\}', 'href={"/uploads/" + report.bliss_file}', content2)
content2 = re.sub(r'src=\{report\.start_photo\}', 'src={"/uploads/" + report.start_photo}', content2)
content2 = re.sub(r'src=\{report\.end_photo\}', 'src={"/uploads/" + report.end_photo}', content2)
content2 = re.sub(r'setZoomedImage\(report\.start_photo\)', 'setZoomedImage("/uploads/" + report.start_photo)', content2)
content2 = re.sub(r'setZoomedImage\(report\.end_photo\)', 'setZoomedImage("/uploads/" + report.end_photo)', content2)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content2)

print("Исправления применены к templates/index.html") 