# Turgutlu Teknoloji Günleri - 5: Görüntü İşleme ile Akıllı Üretim Projesi

**Takım Adı:** [SENİN TAKIM ADIN]

Bu proje, Turgutlu Teknoloji Günleri Hackathon'u için geliştirilmiştir. Amaç, medikal göz pedlerinin kalite kontrolünü görüntü işleme teknikleriyle yapmak, sonuçları mobil bir arayüzde sunmak ve süreci basit bir simülasyonla görselleştirmektir.

## Proje Yapısı

- `/image_processing`: Python tabanlı görüntü işleme modülünü içerir.
- `/mobile_app_flutter`: Flutter ile geliştirilen mobil kullanıcı arayüzünü içerir.
- `/simulation`: Simülasyon görsellerini/dosyalarını içerir (bu projede mobil uygulama içine gömülmüştür).
- `demo_video.mp4`: Projenin 2 dakikalık demo videosu (bağlantısı eklenecek veya dosya yüklenecek).

## 1. Görüntü İşleme Modülü (`/image_processing`)

Bu modül, medikal ped görsellerini analiz ederek kalite kusurlarını tespit eder.

**Kullanılan Teknolojiler:**
- Python
- OpenCV
- NumPy

**Kurulum ve Çalıştırma:**
1. Python 3.x kurulu olmalıdır.
2. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install -r image_processing/requirements_ip.txt
   ```
3. `image_processing/sample_images/` klasörüne test etmek istediğiniz ped görsellerini ekleyin (örn: `my_ped_image.jpg`).
4. `image_processing/image_processor.py` script'indeki `if __name__ == '__main__':` bloğunu aşağıdaki gibi düzenleyin:
   ```python
   if __name__ == '__main__':
       results = analyze_ped_image('sample_images/my_ped_image.jpg')  # Kendi dosya adınızı buraya yazın
       save_results_to_json(results, '../mobile_app_flutter/assets/analysis_results.json')
       print(f"Analiz sonuçları: {results['status']}")
       print(f"Tespit edilen hatalar: {results['errors']}")
       cv2.imshow("İşlenmiş Görüntü", results['processed_image'])
       cv2.waitKey(0)
       cv2.destroyAllWindows()
   ```
   
   Alternatif olarak, görüntünüzü `user_uploads_here.jpg` olarak kaydedip, yukarıdaki kod bloğunu şu şekilde değiştirebilirsiniz:
   ```python
   if __name__ == '__main__':
       results = analyze_ped_image('sample_images/user_uploads_here.jpg')  # Sabit dosya adı
       save_results_to_json(results, '../mobile_app_flutter/assets/analysis_results.json')
       # ... (diğer kodlar aynı kalır)
   ```

**Önemli Not:** Analiz sonuçları JSON formatında `../mobile_app_flutter/assets/analysis_results.json` dosyasına yazılır. Bu dosya, mobil uygulama tarafından okunarak sonuçlar görüntülenir.

**Tespit Edilen Kusurlar:**
- Pedin genel tespiti ve çerçevelenmesi (Whole Recognition)
- Renk farklılıkları (Color Detection)
- Yüzeydeki lekeler (Stain Detection)
- Basit kenar düzensizlikleri (Edge Irregularity - Simplified)
- Basit bütünlük kontrolü (Integrity Check - Simplified)

**Karmaşıklık Analizi (Detaylı):**

*   `detect_ped`: 
    * Zaman Karmaşıklığı: **O(N)**
      * Görüntü okuma: O(N) - N piksel sayısı
      * Gri tonlamaya çevirme: O(N)
      * Eşikleme: O(N)
      * Gauss bulanıklaştırma: O(N) - Her piksel için sabit boyutlu çekirdek kullanılır (5x5)
      * findContours: Ortalama O(N), en kötü durumda O(N²)
      * En büyük konturu bulma: O(K) - K kontur sayısı (genellikle K << N)
    * Mekan Karmaşıklığı: **O(N)**
      * Orijinal görüntü, işlenmiş görüntüler ve maskeler için depolama gerekir

*   `check_color_deviation`:
    * Zaman Karmaşıklığı: **O(R)**
      * HSV dönüşümü: O(R) - R, ROI piksel sayısı
      * inRange: O(R)
      * bitwise_not: O(R)
      * countNonZero: O(R)
    * Mekan Karmaşıklığı: **O(R)**
      * HSV görüntüsü ve maskeler için ek depolama gerekir

*   `check_stains`:
    * Zaman Karmaşıklığı: **O(R)**
      * Gri tonlamaya dönüşüm: O(R) - R, ROI piksel sayısı
      * Eşikleme: O(R)
      * countNonZero: O(R)
    * Mekan Karmaşıklığı: **O(R)**
      * Gri görüntü ve maske için ek depolama

*   `check_edge_irregularity`:
    * Zaman Karmaşıklığı: **O(C)**
      * contourArea: O(C) - C kontur noktası sayısı
      * boundingRect: O(C)
      * Basit aritmetik işlemler: O(1)
    * Mekan Karmaşıklığı: **O(1)**
      * Sadece birkaç değişken için depolama gerektirir

*   `check_integrity_simple`:
    * Zaman Karmaşıklığı: **O(R)**
      * Gri tonlamaya dönüşüm: O(R) - R, ROI piksel sayısı
      * Eşikleme: O(R)
      * countNonZero: O(R)
    * Mekan Karmaşıklığı: **O(R)**
      * Gri görüntü ve maske için ek depolama

*   `analyze_ped_image` (Genel Analiz):
    * Zaman Karmaşıklığı: **O(N + R)**
      * detect_ped: O(N)
      * Diğer kontroller: Her biri O(R), toplam olarak O(R)
      * Kontur işlemleri: O(C) (C << R)
      * Sonuç hazırlama, görüntüye metin ekleme: O(R)
    * Mekan Karmaşıklığı: **O(N + R)**
      * Orijinal görüntü için O(N)
      * İşlenmiş görüntüler ve ROI için O(R)

    *Not: Burada N tüm görüntüdeki piksel sayısını, R ise ilgilenilen bölgedeki (ROI) piksel sayısını, C kontur noktası sayısını ifade eder. Genellikle R < N ve C << R ilişkisi vardır.*

**FPS Ölçümü (Tahmini):**

640x480 çözünürlükte bir görüntü için analiz süreçlerinin ortalama bir dizüstü bilgisayarda tahmini çalışma süreleri:

- Görüntü okuma ve gri tonlamaya çevirme: ~5-10 ms
- Bulanıklaştırma ve eşikleme: ~3-5 ms
- Kontur işlemleri: ~5-10 ms
- ROI çıkarma: ~1-2 ms
- Renk sapması kontrolü: ~5-10 ms
- Leke kontrolü: ~3-7 ms
- Kenar düzensizliği kontrolü: ~2-5 ms
- Bütünlük kontrolü: ~3-7 ms
- Sonuçları hazırlama ve görselleştirme: ~2-5 ms

Toplam işlem süresi: ~30-60 ms (ortalama ~45 ms)

Bu süre yaklaşık **22 FPS** (1000 ms / 45 ms) işleme hızına denk gelir. Daha güçlü işlemcilerde bu değer 30+ FPS'e çıkabilir, düşük donanımlı cihazlarda veya yüksek çözünürlüklü görüntülerle 10-15 FPS'e düşebilir. Mobil cihazlarda ise genellikle 8-15 FPS performans beklenebilir.

*Not: FPS değerleri, kullanılan donanım, görüntü boyutu, arka planda çalışan uygulamalar ve kod optimizasyonuna göre değişkenlik gösterir. Bu tahminler, temel görüntü işleme algoritmalarının tipik performansına dayanmaktadır.*

## 2. Mobil Uygulama (`/mobile_app_flutter`)

Görüntü işleme sonuçlarını kullanıcıya sunan ve etkileşim sağlayan mobil uygulamadır.

**Kullanılan Teknolojiler:**
- Flutter (Dart)

**Kurulum ve Çalıştırma:**
1. Flutter SDK kurulu olmalıdır.
2. Proje klasörüne gidin: `cd mobile_app_flutter`
3. Bağımlılıkları yükleyin: `flutter pub get`
4. Uygulamayı bir emülatörde veya bağlı bir cihazda çalıştırın: `flutter run`

**Çalışma Akışı:**
1. Mobil uygulamada "Görüntü Seç" butonuna basarak bir ped resmi seçin (bu resim sadece uygulamada görüntülenir, analize gönderilmez).
2. Seçtiğiniz resmi (veya benzer bir resmi) `image_processing/sample_images/` klasörüne kopyalayın.
3. Yukarıda açıklandığı gibi Python görüntü işleme modülünü (`image_processor.py`) çalıştırın. Bu işlem analiz sonuçlarını `mobile_app_flutter/assets/analysis_results.json` dosyasına kaydedecektir.
4. Mobil uygulamada "Sonuçları Yükle" butonuna basarak analiz sonuçlarını ve işlenmiş görüntüyü uygulama içinde görüntüleyin.

**Not:** Görüntü işleme modülü ile mobil uygulama arasındaki iletişim şu anda manuel olarak gerçekleştirilmektedir (JSON dosyası aracılığıyla). Bu manuel adım, hackathon süresi kısıtlamasından kaynaklanmaktadır. İleriki sürümlerde, mobil uygulama doğrudan görüntü işleme modülüne erişebilecek şekilde geliştirilebilir.

**Özellikler:**
- Görüntü seçme ve analiz sonuçlarını gösterme.
- Kullanıcı tarafından ayarlanabilir hata eşiği.
- %0 eşik durumu için özel mesaj.
- Basit simülasyon görselleştirmesi (sağlam/hatalı yol).

## 3. Simülasyon

Üretim bandındaki sağlam ve hatalı ürün ayrışması, mobil uygulama içinde statik görsellerle basitleştirilmiş olarak temsil edilmektedir.

## GitHub Paylaşım Etiketi
#ttg5hackathon2025 