# Dönem Ödevi: AWS Üzerinde Ölçeklenebilir DNS Lookup Web Uygulaması

**Ders:** Sanallaştırma ve Bulut Bilişim Teknolojileri

---

## Proje Tanımı

Bu dönem ödevinde, **Python Flask** ile geliştirilmiş bir DNS sorgulama web uygulamasını **Amazon Web Services (AWS)** üzerinde production ortamına deploy edeceksiniz. Uygulama, kullanıcıların domain adreslerini sorgulamasına ve sonuçların MongoDB veritabanına kaydedilmesine olanak sağlar.

Projenin amacı, modern bulut altyapısı, network güvenliği, containerization ve ölçeklenebilir sistem tasarımı konularındaki bilgi ve becerilerinizi pratiğe dökmektir.

---

## Öğrenme Hedefleri

Bu proje sonunda aşağıdaki yetkinliklere sahip olacaksınız:

- AWS VPC, Subnet, Route Table gibi network bileşenlerini yapılandırma
- Public ve Private subnet ayrımı yaparak güvenli network mimarisi tasarlama
- Application Load Balancer (ALB) ve Auto Scaling Group kullanımı
- Docker ve Docker Compose ile containerization
- AWS güvenlik servislerini (Security Groups, IAM, WAF, vb.) entegre etme
- MongoDB veritabanını private subnet'te güvenli şekilde deploy etme
- CloudWatch ile monitoring ve alarm yönetimi
- Production ortamında troubleshooting ve problem çözme

---

## Proje Gereksinimleri

### 1. Uygulama Özellikleri

Geliştirilecek/Deploy edilecek uygulama:

#### **Backend (Python Flask)**
- Domain adreslerini sorgulayan web arayüzü
- DNS lookup işlemi gerçekleştirme (A kayıtları)
- Sorgu sonuçlarını MongoDB'ye kaydetme
- RESTful API endpoint'leri
- Health check endpoint'i (`/health`)
- Ortam değişkenleri ile yapılandırma

#### **Veritabanı (MongoDB)**
- Private subnet'te konumlandırılmış olmalı
- Docker container olarak çalışmalı
- Persistent volume kullanmalı
- Authentication aktif olmalı
- Mongo Express admin arayüzü (opsiyonel, private erişim)

#### **Containerization**
- Docker ve Docker Compose kullanımı zorunlu
- Production-ready Dockerfile
- Health check mekanizmaları
- Logging yapılandırması

---

### 2. AWS Altyapı Gereksinimleri

#### **2.1 Network Mimarisi**

**VPC (Virtual Private Cloud)**
```
CIDR: 10.0.0.0/16
- DNS Support: Enabled
- DNS Hostnames: Enabled
```

**Subnets (Minimum 4 adet - 2 Public, 2 Private)**

| Subnet | CIDR | Availability Zone | Tip | Kullanım |
|--------|------|-------------------|-----|----------|
| Public-1 | 10.0.1.0/24 | us-east-1a | Public | Web Servers |
| Public-2 | 10.0.2.0/24 | us-east-1b | Public | Web Servers |
| Private-1 | 10.0.11.0/24 | us-east-1a | Private | MongoDB Primary |
| Private-2 | 10.0.12.0/24 | us-east-1b | Private | MongoDB Secondary (Opsiyonel) |

**Network Bileşenleri**
- Internet Gateway (IGW)
- NAT Gateway (minimum 1, ideali 2 - her AZ için)
- Route Tables (Public ve Private için ayrı)
- VPC Flow Logs (CloudWatch'a gönderilmeli)

#### **2.2 Compute Resources**

**Web Application Servers (Public Subnet)**
- EC2 Instance Type: `t3.small` veya `t3.micro` (Free Tier)
- AMI: Ubuntu 22.04 LTS veya Amazon Linux 2023
- Port: 5889 (uygulama portu)
- User Data: Otomatik kurulum script'i
- IAM Role: CloudWatch ve SSM izinleri

**MongoDB Server (Private Subnet)**
- EC2 Instance Type: `t3.medium` veya `t3.small`
- AMI: Ubuntu 22.04 LTS
- Port: 27017 (sadece web server'lardan erişilebilir)
- Storage: 20GB EBS Volume (minimum)

#### **2.3 Load Balancing ve Auto Scaling**

**Application Load Balancer (ALB)**
- Type: Application Load Balancer
- Scheme: Internet-facing
- Subnets: Her iki public subnet
- Listener: HTTP (Port 80) → Target Group (Port 5889)
- Health Check: `/health` endpoint'i
- Idle Timeout: 60 seconds

**Target Group**
- Protocol: HTTP
- Port: 5889
- Health Check Path: `/health`
- Health Check Interval: 30 seconds
- Healthy Threshold: 2
- Unhealthy Threshold: 3

**Auto Scaling Group**
- Minimum: 2 instances
- Maximum: 6 instances
- Desired: 2 instances
- Health Check Type: ELB
- Health Check Grace Period: 300 seconds
- Scaling Policy: CPU Utilization > 70%

---

### 3. Güvenlik Gereksinimleri

#### **3.1 Security Groups (Zorunlu)**

**ALB Security Group**
```yaml
Inbound:
  - Port 80 (HTTP) from 0.0.0.0/0
  - Port 443 (HTTPS) from 0.0.0.0/0  # Bonus için

Outbound:
  - Port 5889 to Web Server Security Group
```

**Web Server Security Group**
```yaml
Inbound:
  - Port 5889 from ALB Security Group
  - Port 22 from Bastion/Your IP (yönetim için)

Outbound:
  - Port 27017 to MongoDB Security Group
  - Port 443 to 0.0.0.0/0 (package updates)
  - Port 80 to 0.0.0.0/0 (package updates)
```

**MongoDB Security Group**
```yaml
Inbound:
  - Port 27017 from Web Server Security Group ONLY
  - Port 8081 from Bastion (Mongo Express için, opsiyonel)

Outbound:
  - All traffic (replica set için)
```

#### **3.2 IAM Roles (Zorunlu)**

**EC2 Instance Role**
```json
Permissions:
- CloudWatchAgentServerPolicy (managed policy)
- AmazonSSMManagedInstanceCore (managed policy)
- Custom Policy:
  - logs:CreateLogGroup
  - logs:CreateLogStream
  - logs:PutLogEvents
  - secretsmanager:GetSecretValue (bonus)
```

#### **3.3 AWS Güvenlik Servisleri (Puanlama için gerekli)**

Aşağıdaki servislerden **EN AZ 3 TANESINI** kullanmalısınız:

1. **AWS WAF (Web Application Firewall)** - 5 puan
   - SQL Injection rule
   - Rate limiting rule
   - ALB'ye attach edilmeli

2. **AWS Secrets Manager** - 5 puan
   - MongoDB credentials saklanmalı
   - Uygulamadan Secrets Manager ile credentials okunmalı

3. **VPC Flow Logs** - 3 puan
   - CloudWatch'a gönderilmeli
   - Traffic analizi yapılabilmeli

4. **CloudWatch Alarms** - 4 puan
   - High CPU alarm
   - Unhealthy target alarm
   - SNS bildirimi (email)

5. **AWS Systems Manager - Session Manager** - 3 puan
   - SSH yerine güvenli EC2 erişimi
   - Bastion host'a gerek kalmadan

6. **AWS Config** - Bonus 3 puan
   - Security group compliance
   - Encryption checks

7. **AWS GuardDuty** - Bonus 5 puan
   - Threat detection
   - Anomaly detection

---

### 4. Monitoring ve Logging

#### **CloudWatch (Zorunlu)**

**Log Groups**
- `/aws/ec2/web-application` - Uygulama logları
- `/aws/ec2/mongodb` - MongoDB logları
- `/aws/vpc/flowlogs` - VPC Flow Logs

**Alarms (Minimum 2 adet)**
1. CPU Utilization > 80% (2 evaluation periods)
2. UnHealthyHostCount > 0 (ALB için)

**Dashboard**
- ALB Request Count
- Target Response Time
- EC2 CPU Utilization
- MongoDB Connection Count (opsiyonel)

---

## Teslim Edilecekler

### 1. GitHub Repository (Zorunlu)

Repository Github'a pushlanmak zorunda değil, ITU Kovan'a da konulabilir. Secret'larınızı burada paylaşmadığınızdan emin olunuz.

Repository yapısı:

```
ogrenci-adi-dns-lookup/
│
├── README.md                    # Proje açıklaması, setup guide
├── ARCHITECTURE.md              # Mimari açıklaması
├── DEPLOYMENT-GUIDE.md          # Deployment adımları
│
├── application/                 # Uygulama kodları
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
│
├── infrastructure/              # AWS altyapı scriptleri
│   ├── 01-vpc-setup.sh
│   ├── 02-security-groups.sh
│   ├── 03-mongodb-deployment.sh
│   ├── 04-web-app-deployment.sh
│   ├── 05-load-balancer.sh
│   ├── 06-auto-scaling.sh
│   └── 07-monitoring.sh
│
├── scripts/                     # User data ve helper scriptler
│   ├── mongodb-userdata.sh
│   ├── web-userdata.sh
│   ├── test-deployment.sh
│   └── cleanup.sh
│
├── docs/                        # Dokümantasyon
│   ├── architecture-diagram.png # Mimari şeması (zorunlu)
│   ├── screenshots/             # Ekran görüntüleri
│   │   ├── alb-working.png
│   │   ├── auto-scaling.png
│   │   ├── cloudwatch-dashboard.png
│   │   ├── security-groups.png
│   │   └── web-interface.png
│   ├── troubleshooting.md       # Yaşanan sorunlar ve çözümler
│   └── lessons-learned.md       # Öğrenilen dersler
│
└── presentation/                # Sunum materyalleri
    ├── slides.pdf
    └── demo-video.mp4
```

### 2. Architecture Diagram (Zorunlu)

Aşağıdaki bileşenleri içeren profesyonel bir mimari diyagram:
- VPC ve Subnets
- Internet Gateway ve NAT Gateway
- Load Balancer
- Auto Scaling Group
- EC2 Instances
- MongoDB
- Security Groups (ok ile gösterilmeli)
- Data flow (request-response)

**Önerilen Araçlar:**
- draw.io (ücretsiz)
- Lucidchart
- AWS Architecture Icons kullanın

### 3. Video Demo

5-10 dakikalık demo video:
- Web arayüzü kullanımı
- DNS sorgusu yapılması
- Auto scaling tetiklenmesi
- CloudWatch metrics
- Security yapılandırması

---

## Puanlama Kriterleri

### Temel Gereksinimler (70 Puan)

| Kriter | Puan | Detay |
|--------|------|-------|
| **VPC ve Network** | 15 | VPC, 4 subnet (2 public, 2 private), IGW, NAT Gateway, Route Tables |
| **Security Groups** | 10 | Doğru ve least-privilege kuralları |
| **MongoDB Deployment** | 12 | Private subnet, Docker, persistent volume, authentication |
| **Web App Deployment** | 12 | Docker, doğru env variables, çalışır durumda |
| **Load Balancer** | 8 | ALB, Target Group, Health Check |
| **Auto Scaling** | 8 | ASG, 2-6 instance, CPU based policy |
| **IAM Roles** | 5 | Doğru permissions, least privilege |

### Güvenlik ve Monitoring (25 Puan)

| Kriter | Puan | Detay |
|--------|------|-------|
| **AWS Güvenlik Servisleri** | 15 | 3 servis zorunlu (WAF, Secrets Manager, vb.) |
| **CloudWatch** | 5 | Logs, Alarms (min 2), Dashboard |
| **VPC Flow Logs** | 3 | Aktif ve CloudWatch'a gönderilmeli |
| **SSH Security** | 2 | Bastion host veya SSM Session Manager |

### Dokümantasyon (5 Puan)

| Kriter | Puan | Detay |
|--------|------|-------|
| **README ve DEPLOYMENT-GUIDE** | 2 | Net, adım adım, hatasız |
| **Architecture Diagram** | 2 | Profesyonel, tüm bileşenleri içeriyor |
| **Troubleshooting Doc** | 1 | Yaşanan sorunlar ve çözümler |

### **TOPLAM: 100 Puan**

---

## Bonus Puanlar (Toplam +25 Puan)

| Bonus | Puan | Açıklama |
|-------|------|----------|
| **HTTPS/SSL Certificate** | +5 | ACM sertifikası, HTTPS listener |
| **CI/CD Pipeline** | +5 | GitHub Actions veya CodePipeline |
| **Multi-AZ MongoDB Replica Set** | +5 | 2 AZ'de MongoDB replica |
| **Container Registry (ECR)** | +3 | Docker image ECR'de |
| **Automated Backup** | +2 | MongoDB automated backup stratejisi |
| **Video Demo** | +5 | 5-10 dakikalık profesyonel demo |

**Maksimum Puan: 125/100**

---

## Önemli Tarihler


| Tarih | Olay |
|-------|------|
| [14.11.2025] | Proje teslim tarihi |
| Bilahare Bildirilecek | Final teslim (23:59'a kadar) |

---


---

## Kurallar ve Kısıtlamalar

### İzin Verilenler

- AWS Free Tier kullanımı
- Açık kaynak araçlar ve kütüphaneler
- Online AWS dokümantasyonu ve tutoriallar
- Sınıf içi işbirliği
- Öğretim görevlisine soru sorma
- Her türlü yapay zeka aracına müsaade edilmiştir.

### İzin Verilmeyenler

- Başka kişiler arası kod/script paylaşımı
- Hazır AWS CloudFormation/Terraform template'lerini olduğu gibi kullanma (kendi yazdığınız kabul)
- Plagiarism (intihal) - sıfır tolerans
- AWS kredilerini kötüye kullanma, çözümlerde paylaşılması.

### Maliyet Kontrolü

**UYARI:** AWS kaynaklarını kullanırken dikkatli olun!

```bash
# Billing alarm oluşturun (İLK GÜN)
aws cloudwatch put-metric-alarm \
  --alarm-name student-billing-alarm \
  --alarm-description "Alert at $30" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 30 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:billing-alert
```

**Tavsiyeler:**
- Test bittikten sonra EC2'ları durdurun (terminate değil!)
- NAT Gateway maliyetlidir, gerekmedikçe silin
- EBS snapshot'ları temizleyin
- Kullanmadığınız Elastic IP'leri release edin
- CloudWatch alarm kurun ($3-5 limit)

---

## Başlangıç Adımları

### Adım 1: AWS Account Setup

```bash
# 1. AWS Account oluşturun (zaten varsa atla)
# 2. IAM User oluşturun (AdministratorAccess - sadece ödev için)
# 3. AWS CLI kurun

# macOS
brew install awscli

# Ubuntu/Debian
sudo apt install awscli

# Windows
# https://aws.amazon.com/cli/

# 4. Configure AWS CLI
aws configure
# AWS Access Key ID: [YOUR_ACCESS_KEY]
# AWS Secret Access Key: [YOUR_SECRET_KEY]
# Default region: us-east-1
# Default output: json

# 5. Test et
aws sts get-caller-identity
```

### Adım 2: Repository Oluştur

```bash
# GitHub'da yeni repo oluştur
# Clone et
git clone https://github.com/kullaniciadi/dns-lookup-aws.git
cd dns-lookup-aws

# Klasör yapısını oluştur
mkdir -p application infrastructure scripts docs/screenshots presentation
```

### Adım 3: Uygulamayı İndir ve Test Et

```bash
# Bu repository'deki application dosyalarını kopyala
# Local'de test et (Docker ile)

cd application
docker-compose up -d

# Test
curl http://localhost:5889/health
```

### Adım 4: AWS Deployment'a Başla

```bash
# VPC oluştur (infrastructure/01-vpc-setup.sh)
# Security Groups (infrastructure/02-security-groups.sh)
# ... diğer adımlar
```

---

## Yardım ve Kaynaklar

### Resmi AWS Dokümantasyonu

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Auto Scaling Groups](https://docs.aws.amazon.com/autoscaling/)
- [Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)

### Video Tutoriallar

- AWS VPC Fundamentals
- Docker & Docker Compose Tutorial
- AWS Auto Scaling Deep Dive
- CloudWatch Monitoring Best Practices
- Sizinle önceden paylaştığım Udemy kursları

---

## Teslim Checklist

Teslim etmeden önce kontrol edin:

- [ ] GitHub repository public veya öğretim görevlisine erişim verildi
- [ ] README.md eksiksiz ve güncel
- [ ] Architecture diagram PNG/PDF olarak docs/ altında
- [ ] Tüm infrastructure scriptleri çalışır durumda
- [ ] docker-compose.yml ve Dockerfile production-ready
- [ ] En az 5 screenshot docs/screenshots/ altında
- [ ] Deployment guide adım adım yazılmış
- [ ] CloudWatch dashboard aktif
- [ ] ALB DNS adresi README'de paylaşılmış (demo için)
- [ ] Video demo (bonus için) yüklendi
- [ ] AWS maliyetleri kontrol edildi ve kaynaklar optimize edildi

---

## Yaygın Hatalar (Bunlardan Kaçının!)

1. **Security Group'ta 0.0.0.0/0 her yerde**
   - MongoDB'yi internete açmayın!
   - Sadece gerekli portlar, gerekli kaynaklara

2. **MongoDB credentials hard-coded**
   - Environment variables kullanın
   - Secrets Manager kullanın (bonus)

3. **NAT Gateway unutulması**
   - Private subnet instance'ları internete çıkamaz

4. **Health check endpoint yanlış**
   - `/health` endpoint'i çalışmalı
   - 200 OK dönmeli

5. **Auto Scaling policy yok**
   - Sadece ASG yeterli değil, scaling policy gerekli

6. **Log'lar yok**
   - CloudWatch'a log gönderin
   - Troubleshooting için kritik

7. **Dokümantasyon eksik**
   - README'yi ciddiye alın
   - Deployment guide test edin

8. **Test edilmemiş**
   - Her şeyi test edin
   - Load test yapın

9. **Kaynakları silmeyi unutma**
   - Proje bitince AWS kaynaklarını temizleyin
   - Billing alarm kurun

10. **Son güne bırakma**
    - AWS deployment zaman alır
    - Debugging için süre bırakın

---

## Referans Mimari

### Minimal Gereksinimler (70 puan için)

```
Internet
    │
    ▼
┌───────────────────────────────────────────┐
│              VPC (10.0.0.0/16)            │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │  Public Subnet (10.0.1.0/24)        │ │
│  │  - ALB                               │ │
│  │  - NAT Gateway                       │ │
│  │  - Web EC2 (min 2)                   │ │
│  └─────────────────────────────────────┘ │
│                │                          │
│                ▼                          │
│  ┌─────────────────────────────────────┐ │
│  │  Private Subnet (10.0.11.0/24)      │ │
│  │  - MongoDB EC2                       │ │
│  │  - Mongo Express                     │ │
│  └─────────────────────────────────────┘ │
│                                           │
└───────────────────────────────────────────┘
```

### İdeal Mimari (100+ puan için)

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                  VPC (10.0.0.0/16)                       │
│                                                          │
│  ┌────────────────────┐    ┌────────────────────┐      │
│  │  Public Subnet 1   │    │  Public Subnet 2   │      │
│  │  (AZ1 - 10.0.1.0) │    │  (AZ2 - 10.0.2.0)  │      │
│  │  - NAT GW          │    │  - NAT GW          │      │
│  │  - Web EC2 (ASG)   │    │  - Web EC2 (ASG)   │      │
│  └────────────────────┘    └────────────────────┘      │
│           │                         │                   │
│           └────────── ALB ──────────┘                   │
│                       │                                 │
│                       ▼                                 │
│  ┌────────────────────┐    ┌────────────────────┐     │
│  │  Private Subnet 1  │    │  Private Subnet 2  │     │
│  │  (AZ1 - 10.0.11.0)│    │  (AZ2 - 10.0.12.0) │     │
│  │  - MongoDB Primary │    │  - MongoDB Replica │     │
│  │  - Mongo Express   │    │                    │     │
│  └────────────────────┘    └────────────────────┘     │
│                                                        │
│  Security: WAF, Flow Logs, CloudWatch, Secrets Mgr    │
└────────────────────────────────────────────────────────┘
```

---

## Son Tavsiyeler

1. **Erken başlayın** - AWS'e alışmak zaman alır
2. **Incremental ilerleyin** - Her adımı test edin
3. **Dokümante edin** - Her şeyi not alın
4. **Yedekleyin** - Scriptlerinizi Git'e commit edin
5. **Maliyeti takip edin** - Billing alarm kurun
6. **Soru sorun** - Takıldığınızda yardım isteyin
7. **Test edin** - Her şeyi test edin, sonra tekrar test edin
8. **Cleanup** - Bitince kaynakları silin
9. **Keşfetmenin keyfini çıkartın** - Bu değerli bir öğrenme deneyimi!

---

## Teslim

**Teslim Yöntemi:**
1. Zıp halinde ninova'ya yüklenecektir.
2. Opsiyonel github repo'larınıza yükleyebilirsiniz, bu sizin için güzel bir referans olacaktır.

**Geç Teslim Politikası:**
- 1-24 saat geç: -10 puan
- 24-48 saat geç: -20 puan
- 48 saat sonrası: Kabul edilmez

---

## Başarılar Dileriz!

Bu proje, gerçek dünya cloud deployment deneyimi kazanmanız için tasarlanmıştır. Zorlu olabilir, ama sonunda edindiğiniz bilgi ve beceriler kariyerinizde size çok değerli olacaktır.

**"The cloud is not a place, it's a way of doing IT."** - Paul Maritz

---

**Son Güncelleme:** 14 Kasım 2025  
**Versiyon:** 1.0  
**Öğretim Görevlisi:** Ahmet Tortumlu, Murat Sekmen  
**Bölüm:** Siber Güvenlik MYO
