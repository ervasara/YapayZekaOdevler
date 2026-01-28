import random
import time 

# --- 1. Sınıf: Oda Modeli ---
class Room:
    """Robotun temizleyeceği tek bir odayı temsil eder."""
    def __init__(self, name, is_dirty=False):
        self.name = name
        self.is_dirty = is_dirty

    def clean(self):
        """Odayı temizler."""
        self.is_dirty = False

    def check(self):
        """Odanın kirlilik durumunu döndürür (True=Kirli, False=Temiz)."""
        return self.is_dirty
        
    def soil(self, probability=0.3):
        """Odayı rastgele bir ihtimalle kirletir."""
        # Eğer zaten kirliyse, tekrar kirletmeye çalışma
        if not self.is_dirty and random.random() < probability:
             self.is_dirty = True
             return True
        return False
        
    def get_status_text(self):
        """Oda durumunu anlaşılır metin olarak döndürür."""
        return f"Oda {self.name} ({'KİRLİ' if self.is_dirty else 'Temiz'})"

# --- 2. Sınıf: Robot Modeli (Ajan) ---
class VacuumRobot:
    """Oda durumunu algılayan ve eylem gerçekleştiren robot ajanı."""
    def __init__(self, room_a, room_b):
        self.location = room_a.name  # Başlangıç konumu: "A"
        self.room_a = room_a
        self.room_b = room_b
        self.percept_sequence = []  # Algı listesi
        self.action_list = []      # Eylem listesi

    def get_current_room(self):
        """Robotun o an bulunduğu oda nesnesini döndürür."""
        return self.room_a if self.location == self.room_a.name else self.room_b

    def perceive(self):
        """Robotun bulunduğu odanın durumunu algılar (Percept)."""
        current_room = self.get_current_room()
        dirt_status = current_room.check()
        
        percept = (self.location, dirt_status) # Örnek: ('A', True)
        self.percept_sequence.append(percept)
        return percept

    def decide_and_act(self, percept):
        """Algıya göre karar verir ve eylemi gerçekleştirir."""
        location, is_dirty = percept
        action = "NO_OP (Bekle)"

        if is_dirty:
            # Kirliyse temizle
            action = "CLEAN (Temizle)"
            self.get_current_room().clean()
        else:
            # Temizse diğer odaya geç (left → right veya right → left)
            if location == self.room_a.name:
                action = "MOVE_RIGHT (Sağa Git)"
                self.location = self.room_b.name
            else: # location == self.room_b.name
                action = "MOVE_LEFT (Sola Git)"
                self.location = self.room_a.name
        
        self.action_list.append(action)
        return action
    
    def get_status_report(self):
        """Mevcut durumu ve kayıtları raporlar."""
        return {
            "Percept Dizisi": self.percept_sequence,
            "Eylem Listesi": self.action_list
        }



# --- SIMÜLASYON PARAMETRELERİ ---
MAX_STEPS = 15            # Simülasyonun toplam adım sayısı (Sınır)
STEP_DELAY = 1.0          # Her adım arasındaki gecikme süresi (Saniye)
SOIL_INTERVAL = 3         # Odaların kaç adımda bir kirlilik kontrolü yapılacağı
SOIL_PROBABILITY = 0.5    # Odaların kirlenme ihtimali

# --- BAŞLANGIÇ AYARLARI ---
room_A = Room("A", is_dirty=True) # Başlangıçta A odası kirli
room_B = Room("B", is_dirty=False)
robot = VacuumRobot(room_A, room_B)

current_step = 0

print("="*60)
print(f"     ROBOT SÜPÜRGE AJAN SİMÜLASYONU BAŞLADI")
print(f"     Her Adım Arası Gecikme: {STEP_DELAY} saniye")
print("="*60)
print(f"Başlangıç Durumu: Konum {robot.location}. A:{room_A.get_status_text()}, B:{room_B.get_status_text()}")
print(f"Kirlenme Kontrolü: Her {SOIL_INTERVAL} adımda bir (İhtimal: {SOIL_PROBABILITY * 100:.0f}%)")
print("="*60)


while current_step < MAX_STEPS:
    current_step += 1
    
    print(f"\n--- SİMÜLASYON ADIMI {current_step:02d} / {MAX_STEPS} ({STEP_DELAY:.1f}s bekleme) ---")
    
    # 1. Durum Kaydı (Eylemden Önce)
    loc_before = robot.location
    
    print(f"[BAŞLANGIÇ] Robot Konum: {loc_before}. Oda Durumları: A:{room_A.get_status_text()}, B:{room_B.get_status_text()}")
    
    # 2. Kirlenme Kontrolü
    if current_step % SOIL_INTERVAL == 0:
        a_soiled = room_A.soil(SOIL_PROBABILITY)
        b_soiled = room_B.soil(SOIL_PROBABILITY)
        if a_soiled or b_soiled:
             print(">>>>> ODA KİRLENMESİ GERÇEKLEŞTİ <<<<<")
        
    # 3. Robot Algıla
    percept = robot.perceive()
    location, is_dirty = percept
    
    percept_text = "KİRLİ (True)" if is_dirty else "Temiz (False)"
    print(f"[ALGI] Robot, {location} odasının {percept_text} olduğunu algıladı.")
    
    # 4. Robot Karar Ver ve Eylem Yap
    action = robot.decide_and_act(percept)
    
    print(f"[EYLEM] Robot: {action}")
    
    # 5. Durum Kaydı (Eylemden Sonra)
    loc_after = robot.location
    print(f"[SONUÇ] Yeni Konum: {loc_after}. Oda Durumları: A:{room_A.get_status_text()}, B:{room_B.get_status_text()}")
    
    # ZAMANLAYICI İŞLEMİ: Bir sonraki adıma geçmeden önce bekle
    time.sleep(STEP_DELAY)
    print("-" * 50)


print("\n" + "="*60)
print("     SİMÜLASYON TAMAMLANDI (Maksimum Adım Sınırına Ulaşıldı)")
print("="*60)

# Sonuçların Özeti (İstenen çıktı)
final_report = robot.get_status_report()

print("\n*** PERCEPT SEQUENCE (TÜM ALGI DİZİSİ) ***")
for step, (loc, dirt) in enumerate(final_report["Percept Dizisi"]):
    status = "KİRLİ" if dirt else "TEMİZ"
    print(f"  {step+1:02d}. Algı: (Konum: {loc}, Durum: {status})")

print("\n*** ACTION LIST (TÜM EYLEM LİSTESİ) ***")
for step, action in enumerate(final_report["Eylem Listesi"]):
    print(f"  {step+1:02d}. Eylem: {action}")
print("\n" + "="*60)
