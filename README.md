# AI Clinic - Multi-Agent System

Bu proje, farklı uzmanlık alanlarına sahip AI agent'larını içeren çok dilli bir asistan sistemidir.

## Özellikler

- **Çok Dilli Destek**: Otomatik dil tespiti ve çeviri
- **Uzman Agent'lar**:
  - Matematik Agent'ı: Matematiksel hesaplamalar için
  - Araştırma Agent'ı: Bilgi arama ve araştırma için
  - Genel Asistan: Günlük sohbet ve genel sorular için
- **Akıllı Yönlendirme**: Supervisor agent ile otomatik görev dağıtımı
- **Hafıza**: Konuşma geçmişini kaydetme

## Gereksinimler

```bash
langchain-openai
langchain-core
langgraph
gradio
```

## Kurulum

1. Projeyi klonlayın
2. Gerekli paketleri yükleyin:
   ```bash
   pip install langchain-openai langchain-core langgraph gradio
   ```
3. `config.py` dosyasında OpenAI API anahtarınızı tanımlayın:
   ```python
   openai_api_key = "YOUR_API_KEY_HERE"
   ```

## Kullanım

```bash
python test1.py
```

Program başladıktan sonra sorularınızı yazabilir, sistem otomatik olarak uygun agent'a yönlendirecektir.

## Yapı

- `test1.py`: Ana uygulama dosyası
- `config.py`: API anahtarı konfigürasyonu
- `.gitignore`: Git için göz ardı edilecek dosyalar

## Lisans

Bu proje MIT lisansı altında yayınlanmıştır. 