import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Medikal Ped Kalite Kontrolü',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const QualityControlScreen(),
    );
  }
}

class QualityControlScreen extends StatefulWidget {
  const QualityControlScreen({super.key});

  @override
  State<QualityControlScreen> createState() => _QualityControlScreenState();
}

class _QualityControlScreenState extends State<QualityControlScreen> {
  // Durumu tutacak değişkenler
  String status = '';
  List<String> errors = [];
  bool pedFound = false;
  bool isAnalyzed = false;
  String? imagePath;
  Uint8List? _selectedImageBytes;
  final TextEditingController thresholdController = TextEditingController(text: '5');
  double threshold = 5.0;
  String infoMessage = '';
  String? processedImageBase64;
  bool isLoading = false;
  
  // Toplam kontrol edilen özellik sayısı
  final int totalFeatureCount = 4; // renk, leke, kenar, bütünlük

  final ImagePicker _picker = ImagePicker();

  @override
  void dispose() {
    thresholdController.dispose();
    super.dispose();
  }

  // Görüntü seçme işlevi
  Future<void> _selectImage() async {
    try {
      final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          _selectedImageBytes = bytes;
          imagePath = image.path;
          isAnalyzed = false;
          status = '';
          errors = [];
          processedImageBase64 = null;
          infoMessage = 'Lütfen Python analiz scriptini çalıştırın ve ardından aşağıdaki "Sonuçları Yükle" butonuna basın';
        });
      }
    } catch (e) {
      setState(() {
        infoMessage = 'Görüntü seçilirken hata oluştu: $e';
      });
    }
  }

  // Analiz sonuçlarını yükleme işlevi
    Future<void> _loadAnalysisResults() async {
    setState(() {
      isLoading = true;
      infoMessage = 'Sonuçlar yükleniyor...';
    });

    try {
      // SADECE BU KISIM KALMALI (JSON okumak için)
      String jsonData = await DefaultAssetBundle.of(context).loadString('assets/analysis_results.json');
      
      Map<String, dynamic> results = jsonDecode(jsonData);
      
      setState(() {
        isAnalyzed = true;
        pedFound = results['ped_found'] as bool? ?? false; 
        status = results['status'] as String? ?? 'Bilinmiyor'; 
        errors = List<String>.from(results['errors'] as List? ?? []); 
        
        if (results.containsKey('processed_image_base64')) {
          processedImageBase64 = results['processed_image_base64'] as String?;
        } else {
          processedImageBase64 = null;
        }
        
        _evaluateThreshold();
        infoMessage = '';
      });
    } catch (e) {
      setState(() {
        infoMessage = 'Sonuçlar yüklenirken hata oluştu: $e\n\nLütfen Python scriptinin çalıştırıldığından ve analysis_results.json dosyasının assets klasörüne doğru şekilde kaydedildiğinden emin olun.';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }
  
  // Hata yüzdesine göre durum değerlendirmesi
  void _evaluateThreshold() {
    // Hata yüzdesini hesapla
    double errorPercentage = (errors.length / totalFeatureCount) * 100;
    
    setState(() {
      // Özel kontrol: Eşik %0 ise ve herhangi bir hata varsa
      if (threshold == 0 && errorPercentage > 0) {
        infoMessage = 'Yüzde 0 hatalı ürün bulunmamaktadır';
      } else {
        // Normal kontrol: Hata yüzdesi eşikten düşükse sağlam, yüksekse hatalı
        if (errorPercentage <= threshold) {
          status = 'Sağlam (Eşiğe Göre)';
          infoMessage = '';
        } else {
          status = 'Hatalı (Eşiğe Göre)';
          infoMessage = '';
        }
      }
    });
  }

  // Eşik değerini uygulama
  void _applyThreshold() {
    if (thresholdController.text.isNotEmpty) {
      setState(() {
        threshold = double.tryParse(thresholdController.text) ?? 5.0;
        // Eğer zaten analiz edilmiş bir görüntü varsa, yeni eşik değeriyle tekrar değerlendir
        if (isAnalyzed) {
          _evaluateThreshold();
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Medikal Ped Kalite Kontrolü'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Görüntü seçme butonu
            ElevatedButton(
              onPressed: _selectImage,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 15.0),
              ),
              child: const Text(
                'Görüntü Seç',
                style: TextStyle(fontSize: 16.0),
              ),
            ),
            const SizedBox(height: 10),
            
            // Sonuçları yükleme butonu
            ElevatedButton(
              onPressed: _selectedImageBytes != null ? _loadAnalysisResults : null,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 15.0),
                backgroundColor: Colors.green,
              ),
              child: const Text(
                'Sonuçları Yükle',
                style: TextStyle(fontSize: 16.0),
              ),
            ),
            const SizedBox(height: 20),
            
            // Bilgi mesajı alanı - daha üstte gösterelim
            if (infoMessage.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(5),
                  border: Border.all(color: Colors.blue),
                ),
                child: Text(
                  infoMessage,
                  style: TextStyle(
                    color: infoMessage.contains('hata') ? Colors.red : Colors.blue, 
                    fontWeight: FontWeight.bold
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
            
            if (isLoading)
              const Center(child: CircularProgressIndicator()),
              
            // Görüntü alanı
            Container(
              height: 300,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                border: Border.all(color: Colors.grey),
                borderRadius: BorderRadius.circular(5.0),
              ),
              child: _buildImageWidget(),
            ),
            const SizedBox(height: 20),
            
            // Analiz sonuçları
            Card(
              elevation: 3,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Analiz Sonuçları:',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        const Text('Ped Bulundu: ', style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(isAnalyzed ? (pedFound ? 'Evet' : 'Hayır') : '-'),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Row(
                      children: [
                        const Text('Durum: ', style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(status.isEmpty ? '-' : status,
                            style: TextStyle(
                              color: status.contains('Sağlam') ? Colors.green : 
                                   (status.isNotEmpty ? Colors.red : null),
                              fontWeight: FontWeight.bold
                            )),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Tespit Edilen Hatalar: ', style: TextStyle(fontWeight: FontWeight.bold)),
                        Expanded(
                          child: !isAnalyzed
                              ? const Text('-')
                              : errors.isEmpty
                                  ? const Text('Hata tespit edilmedi')
                                  : Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: errors.map((e) => Text('• $e')).toList(),
                                    ),
                        ),
                      ],
                    ),
                    if (isAnalyzed) ...[
                      const SizedBox(height: 5),
                      Row(
                        children: [
                          const Text('Hata Oranı: ', style: TextStyle(fontWeight: FontWeight.bold)),
                          Text('${((errors.length / totalFeatureCount) * 100).toStringAsFixed(1)}%'),
                        ],
                      ),
                      Row(
                        children: [
                          const Text('Belirlenen Eşik: ', style: TextStyle(fontWeight: FontWeight.bold)),
                          Text('$threshold%'),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            
            // Hata eşiği ayarı
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: thresholdController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Hata Eşiği (%)',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _applyThreshold,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
                  ),
                  child: const Text('Uygula'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  // Görüntü widget'ı oluşturma fonksiyonu
  Widget _buildImageWidget() {
    if (processedImageBase64 != null && processedImageBase64!.isNotEmpty) {
      // İşlenmiş görüntüyü base64'ten decode edip göster
      try {
        final Uint8List bytes = base64Decode(processedImageBase64!);
        return Image.memory(bytes, fit: BoxFit.contain);
      } catch (e) {
        return Center(child: Text('İşlenmiş görüntü gösterilemiyor: $e'));
      }
    } else if (_selectedImageBytes != null) {
      // Seçilen görüntüyü byte'lardan göster
      return Image.memory(_selectedImageBytes!, fit: BoxFit.contain);
    } else {
      // Henüz hiçbir görüntü seçilmemiş
      return const Center(child: Text('Görüntü burada gösterilecek'));
    }
  }
} 
 