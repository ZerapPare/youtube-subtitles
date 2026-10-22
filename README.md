# ถอดซับ YouTube

เว็บสำหรับดึงซับไตเติลที่มีอยู่แล้วในคลิป YouTube ออกมาทั้งคลิป แค่วางลิงก์ก็ใช้ได้

## เปิดให้เข้าจากที่ไหนก็ได้ (ฟรี)

ดับเบิลคลิก **`start.bat`**

- ครั้งแรกจะติดตั้ง Python packages และดาวน์โหลด `cloudflared` มาไว้ใน `.tools/` ให้อัตโนมัติ
- จะได้ลิงก์ `https://xxxx.trycloudflare.com` (copy ไว้ให้แล้ว) ส่งให้ใครก็เปิดได้
- ปิดหน้าต่างเมื่อไหร่ เว็บก็ปิดด้วย
- ลิงก์จะเปลี่ยนทุกครั้งที่เปิดใหม่ และคอมต้องเปิดอยู่ตลอดเวลาที่มีคนใช้

ใช้ IP บ้านในการดึงซับ จึงไม่โดน YouTube บล็อกเหมือนเซิร์ฟเวอร์คลาวด์

## รันบนเครื่องอย่างเดียว

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

จากนั้นเปิด http://127.0.0.1:5000

## Deploy บน Vercel (ต้องใช้ proxy แบบเสียเงิน)

โปรเจกต์นี้ใช้ Flask แบบ zero-config ของ Vercel ได้เลย
- `app.py` คือ Flask app (Vercel จะ detect อัตโนมัติ) รับ `/api/*`
- `public/index.html` เป็นหน้าเว็บที่ Vercel เสิร์ฟผ่าน CDN

```bash
npm i -g vercel
vercel          # preview
vercel --prod   # production
```

หรือ push ขึ้น GitHub แล้ว Import โปรเจกต์ใน vercel.com

### ⚠️ ต้องตั้งค่า proxy

YouTube บล็อก IP ของผู้ให้บริการคลาวด์เกือบทั้งหมด (รวมถึง Vercel) ถ้าไม่ตั้ง proxy
เว็บที่ deploy แล้วจะขึ้น "YouTube บล็อกการเชื่อมต่อจากเซิร์ฟเวอร์นี้"

ตั้ง Environment Variables ใน Vercel (Project → Settings → Environment Variables) อย่างใดอย่างหนึ่ง:

| ตัวแปร | ใช้เมื่อ |
| --- | --- |
| `WEBSHARE_PROXY_USERNAME`, `WEBSHARE_PROXY_PASSWORD` | ใช้ [Webshare](https://www.webshare.io/) แบบ Residential (แนะนำ) |
| `PROXY_URL` | proxy อื่นๆ เช่น `http://user:pass@host:port` |

## ความสามารถ

- รองรับลิงก์หลายแบบ: `watch?v=`, `youtu.be/`, `shorts/`, `live/`, `embed/` หรือใส่แค่ video ID
- เลือกภาษาซับได้ (ทั้งซับที่ผู้สร้างใส่เองและซับอัตโนมัติ) ถ้ามีภาษาไทยจะเลือกให้ก่อน
- กดที่เวลาเพื่อข้ามไปดูช่วงนั้นในคลิป
- ค้นหาคำในซับ, แสดงแบบมีเวลา / ไม่มีเวลา / ย่อหน้า
- คัดลอก หรือดาวน์โหลดเป็น `.txt` / `.srt`
- โหมดสว่าง/มืด (ตามระบบ หรือกดสลับเองได้)
