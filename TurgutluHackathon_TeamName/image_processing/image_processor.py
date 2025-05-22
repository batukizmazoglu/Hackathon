import cv2
import numpy as np
import json # JSON işlemleri için eklendi
import base64 # Base64 çevrimi için eklendi

def detect_ped(image_path):
    """
    Verilen görüntüdeki en büyük beyaz/açık renkli dikdörtgen alanı (göz pedi) tespit eder
    ve etrafına bir çerçeve çizer.
    Pedin konumunu (x, y, w, h) ve çerçevelenmiş görüntüyü döndürür.
    Eğer ped bulunamazsa None, None döndürür.
    """
    try:
        # 1. Görüntüyü oku
        image = cv2.imread(image_path)
        if image is None:
            print(f"HATA: Görüntü okunamadı veya bulunamadı: {image_path}")
            return None, None
            
        output_image = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, light_mask = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(light_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print("UYARI: Hiçbir kontur bulunamadı.")
            return None, None
        
        largest_contour = max(contours, key=cv2.contourArea)
        min_area = 1000
        if cv2.contourArea(largest_contour) < min_area:
            print(f"UYARI: En büyük kontur çok küçük: {cv2.contourArea(largest_contour)} < {min_area}")
            return None, None
        
        x, y, w, h = cv2.boundingRect(largest_contour)
        cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return (x, y, w, h), output_image
        
    except Exception as e:
        print(f"detect_ped HATA: {str(e)}")
        return None, None

def check_color_deviation(image_roi, reference_color_hsv_lower=np.array([0, 0, 180]), reference_color_hsv_upper=np.array([180, 30, 255])):
    if image_roi is None or image_roi.size == 0:
        print("check_color_deviation UYARI: ROI boş.")
        return None
    try:
        hsv_roi = cv2.cvtColor(image_roi, cv2.COLOR_BGR2HSV)
        in_range_mask = cv2.inRange(hsv_roi, reference_color_hsv_lower, reference_color_hsv_upper)
        out_of_range_mask = cv2.bitwise_not(in_range_mask)
        out_of_range_pixels = cv2.countNonZero(out_of_range_mask)
        total_pixels = image_roi.shape[0] * image_roi.shape[1]
        if total_pixels == 0: return None # Bölme hatasını önle
        deviation_ratio = out_of_range_pixels / total_pixels
        deviation_threshold = 0.05
        if deviation_ratio > deviation_threshold:
            return 'Renk Hatası'
        return None
    except Exception as e:
        print(f"check_color_deviation HATA: {e}")
        return None

def check_stains(image_roi, stain_threshold_value=100, min_stain_area_ratio=0.01):
    if image_roi is None or image_roi.size == 0:
        print("check_stains UYARI: ROI boş.")
        return None
    try:
        gray_roi = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        _, stain_mask = cv2.threshold(gray_roi, stain_threshold_value, 255, cv2.THRESH_BINARY_INV)
        stain_pixels = cv2.countNonZero(stain_mask)
        total_pixels = image_roi.shape[0] * image_roi.shape[1]
        if total_pixels == 0: return None
        stain_ratio = stain_pixels / total_pixels
        if stain_ratio > min_stain_area_ratio:
            return 'Leke Tespit Edildi'
        return None
    except Exception as e:
        print(f"check_stains HATA: {e}")
        return None

def check_edge_irregularity(ped_contour, expected_aspect_ratio_range=(2.0, 3.0), min_area_for_check=1000):
    if ped_contour is None:
        print("check_edge_irregularity UYARI: Kontur yok.")
        return None
    try:
        area = cv2.contourArea(ped_contour)
        if area < min_area_for_check:
            return None
        x, y, w, h = cv2.boundingRect(ped_contour)
        if h == 0: return None
        aspect_ratio = w / h
        if aspect_ratio < expected_aspect_ratio_range[0] or aspect_ratio > expected_aspect_ratio_range[1]:
            return 'Kesim Hatası (Oran)'
        return None
    except Exception as e:
        print(f"check_edge_irregularity HATA: {e}")
        return None

def check_integrity_simple(image_roi, dark_threshold=50, min_defect_area_ratio=0.02):
    if image_roi is None or image_roi.size == 0:
        print("check_integrity_simple UYARI: ROI boş.")
        return None
    try:
        gray_roi = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        _, defect_mask = cv2.threshold(gray_roi, dark_threshold, 255, cv2.THRESH_BINARY_INV)
        defect_pixels = cv2.countNonZero(defect_mask)
        total_pixels = image_roi.shape[0] * image_roi.shape[1]
        if total_pixels == 0: return None
        defect_ratio = defect_pixels / total_pixels
        if defect_ratio > min_defect_area_ratio:
            return 'Yapısal Bozulma Şüphesi'
        return None
    except Exception as e:
        print(f"check_integrity_simple HATA: {e}")
        return None

def analyze_ped_image(image_path):
    result = {
        'ped_found': False,
        'ped_coords': None,
        'status': 'Bilinmiyor', # Başlangıç değeri
        'errors': [],
        'processed_image': None
    }
    
    ped_coords, processed_image = detect_ped(image_path)
    
    if ped_coords is None or processed_image is None:
        print(f"analyze_ped_image: {image_path} için ped tespit edilemedi.")
        return result # Ped bulunamazsa direkt boş sonuç dön
    
    result['ped_found'] = True
    result['ped_coords'] = ped_coords
    result['processed_image'] = processed_image.copy() # processed_image'in kopyasını al
    
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"analyze_ped_image: {image_path} orijinali okunamadı (ROI için).")
        result['status'] = 'Hatalı (Görüntü Okuma Sorunu)'
        return result

    x, y, w, h = ped_coords
    
    # ROI kesilirken koordinatların görüntü sınırları içinde olduğundan emin ol
    if y + h > original_image.shape[0] or x + w > original_image.shape[1]:
        print("analyze_ped_image UYARI: ROI koordinatları görüntü sınırlarının dışında.")
        ped_roi = None
    else:
        ped_roi = original_image[y:y+h, x:x+w]

    if ped_roi is not None and ped_roi.size > 0:
        color_error = check_color_deviation(ped_roi)
        if color_error: result['errors'].append(color_error)
        
        stain_error = check_stains(ped_roi)
        if stain_error: result['errors'].append(stain_error)
        
        # Kenar kontrolü için ped konturunu tekrar bulmaya gerek yok, detect_ped'den gelen koordinatlar yeterli olabilir
        # Ancak check_edge_irregularity bir kontur bekliyor. detect_ped'den konturu döndürmesini sağlamak daha iyi olur.
        # Şimdilik basit bir kontrol yapalım ya da bu adımı atlayalım eğer kontur yoksa.
        # En iyisi detect_ped'den konturu da döndürmek. Şimdilik bu kısmı geçici olarak devre dışı bırakalım.
        # ----
        # gray_roi_for_contour = cv2.cvtColor(ped_roi, cv2.COLOR_BGR2GRAY)
        # _, thresh_roi_for_contour = cv2.threshold(gray_roi_for_contour, 180, 255, cv2.THRESH_BINARY)
        # contours_in_roi, _ = cv2.findContours(thresh_roi_for_contour, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # if contours_in_roi:
        #     largest_contour_in_roi = max(contours_in_roi, key=cv2.contourArea)
        #     edge_error = check_edge_irregularity(largest_contour_in_roi) # Bu kontur ROI'ye göre, tüm görüntüye göre değil.
        #     if edge_error: result['errors'].append(edge_error)
        # ----
        # Daha basit bir kenar kontrolü (aspect ratio):
        if h != 0:
            aspect_ratio = w / h
            expected_aspect_ratio_range=(1.5, 4.0) # Göz pedi için daha geniş bir aralık olabilir
            if not (expected_aspect_ratio_range[0] <= aspect_ratio <= expected_aspect_ratio_range[1]):
                result['errors'].append(f'Kesim Hatası (Oran: {aspect_ratio:.2f})')


        integrity_error = check_integrity_simple(ped_roi)
        if integrity_error: result['errors'].append(integrity_error)
    else:
        print("analyze_ped_image UYARI: Ped ROI oluşturulamadı veya boş.")
        result['errors'].append("ROI Hatası")

    if result['errors']:
        result['status'] = 'Hatalı'
    else:
        result['status'] = 'Sağlam'
    
    # Hataları görüntü üzerine yazdırma
    # processed_image'in kopyası zaten result['processed_image'] içinde var
    display_image_with_text = result['processed_image'] # .copy() gerekmez, çünkü zaten kopyalandı
    
    # Yazıların pedin koordinatlarına göre yerleştirilmesi
    text_x, text_y_start = x, y 
    y_offset_val = 20 # Yazılar arası dikey boşluk
    font_scale_val = 0.6
    thickness_val = 1
    
    if not result['errors']:
        cv2.putText(display_image_with_text, "Saglam", (text_x, text_y_start - 5 if text_y_start - 5 > 0 else text_y_start + h + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale_val, (0, 255, 0), thickness_val)
    else:
        for i, error_msg in enumerate(result['errors']):
            current_text_y = text_y_start - 5 - (i * y_offset_val)
            if current_text_y < 10 : # Eğer yazılar görüntünün çok üstüne çıkıyorsa
                current_text_y = text_y_start + h + 15 + (i * y_offset_val) # Pedin altına yaz
            cv2.putText(display_image_with_text, error_msg, (text_x, current_text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale_val, (0, 0, 255), thickness_val)
    
    result['processed_image'] = display_image_with_text
    return result

def save_results_to_json(results_dict, output_path='analysis_results.json'):
    """
    Analiz sonuçlarını bir JSON dosyasına kaydeder.
    İşlenmiş görüntüyü base64 string olarak kaydeder.
    """
    # NumPy array'lerini ve tuple'ları JSON serileştirilebilir formatlara dönüştür
    results_to_save = {}
    for key, value in results_dict.items():
        if isinstance(value, np.ndarray):
            # processed_image için base64 çevrimi
            if key == 'processed_image':
                if value is not None and value.size > 0:
                    is_success, buffer = cv2.imencode(".png", value)
                    if is_success:
                        results_to_save['processed_image_base64'] = base64.b64encode(buffer).decode('utf-8')
                    else:
                        results_to_save['processed_image_base64'] = None
                else:
                    results_to_save['processed_image_base64'] = None
            else:
                # Diğer NumPy array'leri (örn: HSV değerleri) liste olarak kaydedilebilir
                results_to_save[key] = value.tolist()
        elif isinstance(value, tuple):
            results_to_save[key] = list(value)
        else:
            results_to_save[key] = value
    
    # Orijinal 'processed_image' anahtarını (NumPy array olan) silelim, sadece base64 kalsın
    if 'processed_image' in results_to_save and 'processed_image_base64' in results_to_save :
         del results_to_save['processed_image']

    try:
        with open(output_path, 'w') as f:
            json.dump(results_to_save, f, indent=4)
        print(f"BİLGİ: Sonuçlar '{output_path}' dosyasına kaydedildi.")
    except Exception as e:
        print(f"save_results_to_json HATA: JSON dosyasına yazılırken hata: {e}")

if __name__ == '__main__':
    # LÜTFEN DİKKAT:
    # 1. `image_processing` klasörü içinde `sample_images` adında bir klasör oluşturun.
    # 2. Bu `sample_images` klasörünün içine test etmek istediğiniz bir göz pedi resmini
    #    `my_ped_image.jpg` (veya aşağıdaki değişkende belirttiğiniz başka bir isimle) kopyalayın.

    image_file_to_test = r'C:\Projeler\HACKATHON\TurgutluHackathon_TeamName\image_processing\sample_images\my_ped_image.jpg'  # Test edilecek resmin yolu ve adı
                                                        # Bu dosya `image_processing/sample_images/` altında olmalı.

    # Görüntü işleme modülünün bulunduğu dizinden çalıştırıldığını varsayıyoruz.
    # Eğer ana proje dizininden çalıştırıyorsanız:
    # image_file_to_test = 'image_processing/sample_images/my_ped_image.jpg'

    print(f"BİLGİ: '{image_file_to_test}' analiz ediliyor...")
    results = analyze_ped_image(image_file_to_test)

    if results and results.get('ped_found'):
        print(f"  Durum: {results.get('status')}")
        print(f"  Hatalar: {results.get('errors')}")

        # JSON'a kaydet (Flutter assets klasörüne)
        # Bu script `image_processing` klasöründen çalıştırıldığı için ../ ile bir üst dizine çıkıyoruz.
        json_output_path = r'mobile_app_flutter/assets/analysis_results.json'
        save_results_to_json(results, json_output_path)

        # İşlenmiş görüntüyü göster
        if results.get('processed_image_base64'): # Base64'e çevrildiyse, orijinal numpy array'i göstermek yerine
                                               # (ki o artık 'processed_image' anahtarında olmayabilir)
                                               # doğrudan base64'ten decode edip göstermeyelim,
                                               # analyze_ped_image'dan dönen numpy array'i (eğer hala varsa) veya
                                               # detect_ped'den gelen ilk işlenmiş görüntüyü gösterelim.
                                               # Ya da en iyisi, analyze_ped_image içinde en son metin eklenmiş
                                               # numpy array'i alıp onu gösterelim.

            # analyze_ped_image zaten en son halini döndürüyor 'processed_image' numpy array olarak
            final_display_image = results.get('processed_image') # Bu, metinlerin yazıldığı NumPy array olmalı.
            if final_display_image is not None and final_display_image.size > 0:
                 cv2.imshow(f"İşlenmiş Görüntü: {image_file_to_test}", final_display_image)
                 print("BİLGİ: Görüntü penceresini kapatmak için herhangi bir tuşa basın.")
                 cv2.waitKey(0) # Bir tuşa basılana kadar bekle
            else:
                print("UYARI: Gösterilecek işlenmiş görüntü bulunamadı (NumPy array).")

    else:
        print(f"UYARI: Ped tespit edilemedi veya '{image_file_to_test}' için analizde bir sorun oluştu.")

    cv2.destroyAllWindows()
    print("BİLGİ: Script tamamlandı.")