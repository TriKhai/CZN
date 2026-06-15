import csv
import os
import re
import time
from io import BytesIO
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
from PIL import Image

# Cấu hình đường dẫn và thư mục lưu trữ
URL = "https://www.czncompass.com/en/equipment"
IMAGE_FOLDER = "czn_equipment_images"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.czncompass.com/",
}

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def download_image_as_pil(url):
    if not url or not url.startswith("http"):
        return None
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            return img.convert("RGBA")
    except Exception as e:
        print(f" [!] Lỗi tải ảnh: {e}")
    return None

def crawl_data():
    all_rendered_htmls = []

    with sync_playwright() as p:
        print("Đang khởi chạy trình duyệt giả lập...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": headers["User-Agent"]})

        print(f"Đang truy cập liên kết gốc: {URL}")
        page.goto(URL, wait_until="networkidle")
        time.sleep(4)

        page_count = 1
        while True:
            print(f"--- Đang xử lý và nạp dữ liệu trang {page_count} ---")
            all_rendered_htmls.append(page.content())

            next_btn = page.locator("button:has-text('Next').flex.items-center")
            if next_btn.count() > 1:
                next_btn = next_btn.last

            if next_btn.is_visible():
                if next_btn.is_disabled():
                    print(" Đã chạm tới trang cuối cùng.")
                    break
                try:
                    print("Đang click chuyển sang trang tiếp theo...")
                    next_btn.click(timeout=5000)
                    time.sleep(4)
                    page_count += 1
                except Exception:
                    break
            else:
                break

        browser.close()

    print(f"\n Đã nạp xong {len(all_rendered_htmls)} trang HTML. Bắt đầu phân tích & bóc tách sâu...")
    all_data = []
    seen_names = set()

    for html_content in all_rendered_htmls:
        soup = BeautifulSoup(html_content, "html.parser")
        buttons = soup.find_all("button", class_=lambda x: x and "text-left" in x and "cursor-pointer" in x)
        
        for idx, btn in enumerate(buttons):
            try:
                # 1. Lấy tên trang bị
                h3_tag = btn.find("h3")
                if not h3_tag:
                    continue
                name = h3_tag.text.strip()
                
                if name in seen_names:
                    continue
                seen_names.add(name)

                safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")

                # 2. Bóc tách link ảnh khung nền & Phân loại độ hiếm (Level)
                bg_url = ""
                equip_level = "Rare" # Mặc định dự phòng
                
                div_with_bg = btn.find("div", style=lambda x: x and "background-image" in x and "rarity" in x)
                if div_with_bg:
                    style_str = div_with_bg.get("style", "")
                    match = re.search(r'url\((?:&quot;|"|\')?(.*?)(?:&quot;|"|\')?\)', style_str)
                    if match:
                        bg_url = match.group(1)
                        # Chuẩn hóa độ hiếm dựa vào tên tệp ảnh nền
                        bg_url_lower = bg_url.lower()
                        if "unique" in bg_url_lower or "epic" in bg_url_lower:
                            equip_level = "Mystic"
                        elif "legend" in bg_url_lower:
                            equip_level = "Legend"
                        elif "rare" in bg_url_lower:
                            equip_level = "Rare"

                # 3. Phân loại Loại trang bị (Type) từ thẻ icon cạnh tên h3
                equip_type = "Trinket" # Mặc định dự phòng
                # Tìm thẻ span chứa img icon loại trang bị trước thẻ h3
                type_span = btn.find("span", class_=lambda x: x and "border" in x and "bg-" in x)
                if type_span and type_span.find("img"):
                    alt_type = type_span.find("img").get("alt", "").strip().lower()
                    if "weapon" in alt_type:
                        equip_type = "Weapon"
                    elif "armor" in alt_type or "amor" in alt_type:
                        equip_type = "Armor"
                    elif "trinket" in alt_type:
                        equip_type = "Trinket"

                # 4. Bóc tách link ảnh trang bị gốc
                img_tags = btn.find_all("img")
                img_url = ""
                for img in img_tags:
                    alt_text = img.get("alt", "")
                    if alt_text.lower() == name.lower() or "relics" in img.get("src", "") or "item" in img.get("src", ""):
                        img_url = img.get("src") or ""
                        break
                if not img_url and img_tags:
                    img_url = img_tags[0].get("src") or ""

                if img_url.startswith("/"):
                    img_url = "https://www.czncompass.com" + img_url

                # 5. Lấy dòng mô tả hiệu ứng
                p_effect = btn.find("p", class_=lambda x: x and "text-gray-100" in x)
                effect = p_effect.text.strip() if p_effect else "Không có hiệu ứng"

                # 6. Lấy địa điểm Map Chaos (Tách lọc thông minh)
                p_map = btn.find("p", class_=lambda x: x and "text-gray-400" in x and "text-[8px]" in x)
                if p_map:
                    lines = [line.strip() for line in p_map.get_text(separator="\n").split("\n") if line.strip()]
                    final_maps = []
                    for line in lines:
                        if "/" in line:
                            final_maps.extend([m.strip() for m in line.split("/") if m.strip()])
                        else:
                            final_maps.append(line)
                    chaos_map = ", ".join(final_maps)
                else:
                    chaos_map = "Unknown Map"

                # 7. Xử lý đồ họa ghép ảnh tự động
                local_img_path = "Không có ảnh"
                if img_url and "http" in img_url:
                    item_img = download_image_as_pil(img_url)
                    if item_img:
                        bg_img = download_image_as_pil(bg_url) if bg_url else None
                        filename = f"{safe_name}.png"
                        file_path = os.path.join(IMAGE_FOLDER, filename)
                        
                        if bg_img:
                            bg_w, bg_h = bg_img.size
                            item_size = int(bg_w * 0.75)
                            item_img_resized = item_img.resize((item_size, item_size), Image.Resampling.LANCZOS)
                            offset_x = (bg_w - item_size) // 2
                            offset_y = (bg_h - item_size) // 2 - int(bg_h * 0.05) 
                            
                            final_canvas = Image.new("RGBA", bg_img.size)
                            final_canvas.paste(bg_img, (0, 0))
                            final_canvas.paste(item_img_resized, (offset_x, offset_y), item_img_resized)
                            final_canvas.save(file_path, "PNG")
                        else:
                            item_img.save(file_path, "PNG")
                            
                        local_img_path = file_path

                all_data.append({
                    "Tên trang bị": name,
                    "Loại": equip_type,       # Cột mới phân loại Weapon/Armor/Trinket
                    "Độ hiếm": equip_level,   # Cột mới phân loại Mystic/Legend/Rare
                    "Hiệu ứng / Kỹ năng": effect,
                    "Map Chaos": chaos_map,
                    "Vị trí file ảnh PNG hoàn chỉnh": local_img_path
                })
                
            except Exception as e:
                print(f" Lỗi xử lý ở trang bị {name if 'name' in locals() else idx}: {e}")

    # Xuất toàn bộ danh sách tổng hợp ra Excel CSV
    with open("data_trang_bi_czn.csv", mode="w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["Tên trang bị", "Loại", "Độ hiếm", "Hiệu ứng / Kỹ năng", "Map Chaos", "Vị trí file ảnh PNG hoàn chỉnh"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
        
    print(f"\n=== ĐÃ HOÀN THÀNH CÀO VÀ PHÂN LOẠI CHI TIẾT ===")
    print(f"- Tổng số lượng trang bị thu thập: {len(all_data)}")

if __name__ == "__main__":
    crawl_data()