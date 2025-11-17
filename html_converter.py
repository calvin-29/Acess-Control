import sys
import base64
import ast

file_path = sys.argv[1]
info = ast.literal_eval(sys.argv[2])

with open(file_path, "w", encoding="utf-8") as e:
    e.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Control Records</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #0078d7; color: white; }
        img { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; }
    </style>
</head>
<body>
    <h2>Access Control Records</h2>
    <table>
        <thead>
            <tr>
                <th>Tag</th>
                <th>Name</th>
                <th>Address</th>
                <th>Phone number</th>
                <th>Purpose</th>
                <th>Who to meet</th>
                <th>Time In</th>
                <th>Time Out</th>
                <th>Date</th>
                <th>Picture</th>
            </tr>
        </thead>
        <tbody>
""")
    for row in info:
        tag, name, address, phone, purpose, who, time_in, time_out, date, picture = row
        if picture:
            img_data = base64.b64encode(picture).decode("utf-8")
            img_tag = f'<img src="data:image/jpeg;base64,{img_data}">'
        else:
            img_tag = '<span style="color:#888;">No Image</span>'

        e.write(f"""
            <tr>
                <td>{tag or ''}</td>
                <td>{name or ''}</td>
                <td>{address or ''}</td>
                <td>{phone or ''}</td>
                <td>{purpose or ''}</td>
                <td>{who or ''}</td>
                <td>{time_in or ''}</td>
                <td>{time_out or ''}</td>
                <td>{date or ''}</td>
                <td>{img_tag}</td>
            </tr>
""")
        e.write("""
        </tbody>
    </table>
</body>
</html>
""")
