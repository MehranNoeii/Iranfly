import mysql.connector

from config import database_config, database_name


def create_database():
    db = mysql.connector.connect(**database_config)
    cursor = db.cursor()

    cursor.execute(
        f"""
        CREATE DATABASE IF NOT EXISTS {database_name}
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        """
    )

    cursor.close()
    db.close()


def connect_db():
    config = database_config.copy()
    config['database'] = database_name

    return mysql.connector.connect(**config)


# ===========================
# USERS
# ===========================

def create_table_users():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            cid BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            national_code CHAR(10) UNIQUE,
            birth_date DATE,
            gender ENUM('male','female'),
            phone_number VARCHAR(15) UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# AIRLINES
# ===========================

def create_table_airlines():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airlines(
            airline_id INT AUTO_INCREMENT PRIMARY KEY,
            airline_name VARCHAR(100) UNIQUE
        )
    """)

    db.commit()
    cursor.close()
    db.close()



def insert_default_airlines():

    db = connect_db()
    cursor = db.cursor()

    airlines = [

        "ایران ایر",
        "ماهان ایر",
        "آتا ایر",
        "کیش ایر",
        "قشم ایر",
        "ترکیش ایرلاینز",
        "امارات",
        "قطر ایرویز",
        "پگاسوس",
        "فلای دبی"
    ]

    for airline in airlines:

        cursor.execute(
            """
            SELECT airline_id
            FROM airlines
            WHERE airline_name=%s
            """,
            (airline,)
        )

        if not cursor.fetchone():

            cursor.execute(
                """
                INSERT INTO airlines
                (airline_name)
                VALUES(%s)
                """,
                (airline,)
            )

    db.commit()
    cursor.close()
    db.close()


# ===========================
# AIRPORTS
# ===========================


def create_table_airports():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airports(
            airport_id INT AUTO_INCREMENT PRIMARY KEY,

            airport_name VARCHAR(100),

            city VARCHAR(50),

            country VARCHAR(50),

            airport_type ENUM(
                'domestic',
                'international',
                'both'
            )
        )
    """)

    db.commit()
    cursor.close()
    db.close()


def insert_default_airports():

    db = connect_db()
    cursor = db.cursor()

    airports = [

        ("مهرآباد","تهران","ایران","domestic"),
        ("امام خمینی","تهران","ایران","international"),
        ("هاشمی نژاد","مشهد","ایران","both"),
        ("شهید بهشتی","اصفهان","ایران","both"),
        ("شهید دستغیب","شیراز","ایران","both"),
        ("شهید مدنی","تبریز","ایران","both"),
        ("بین المللی","اهواز","ایران","both"),
        ("بین المللی","کیش","ایران","both"),
        ("بین المللی","قشم","ایران","both"),
        ("بین المللی","بندرعباس","ایران","both"),
        ("هاشمی نژاد","کرمان","ایران","both"),
        ("شهید صدوقی","یزد","ایران","both"),
        ("سردار جنگل","رشت","ایران","both"),
        ("دشت ناز","ساری","ایران","both"),
        ("شهید باکری","ارومیه","ایران","both"),
        ("بین المللی","زاهدان","ایران","both"),
        ("شهید اشرفی","کرمانشاه","ایران","both"),
        ("سنندج","سنندج","ایران","both"),
        ("بوشهر","بوشهر","ایران","both"),
        ("گرگان","گرگان","ایران","both"),

        ("دبی","دبی","امارات","international"),
        ("آل مکتوم","دبی","امارات","international"),
        ("آتاتورک","استانبول","ترکیه","international"),
        ("صبیحه گوکچن","استانبول","ترکیه","international"),
        ("حمد","دوحه","قطر","international"),
        ("بین المللی","مسقط","عمان","international"),
        ("بین المللی","کویت","کویت","international"),
        ("حیدر علیاف","باکو","آذربایجان","international"),
        ("شوتا روستاولی","تفلیس","گرجستان","international"),
        ("زوارتنوتس","ایروان","ارمنستان","international"),

        ("برلین","برلین","آلمان","international"),
        ("فرانکفورت","فرانکفورت","آلمان","international"),
        ("لندن","لندن","انگلستان","international"),
        ("پاریس","پاریس","فرانسه","international"),
        ("رم","رم","ایتالیا","international"),
        ("میلان","میلان","ایتالیا","international"),
        ("بارسلونا","بارسلونا","اسپانیا","international"),
        ("مادرید","مادرید","اسپانیا","international"),
        ("آمستردام","آمستردام","هلند","international"),
        ("وین","وین","اتریش","international"),
        ("زوریخ","زوریخ","سوئیس","international"),
        ("استکهلم","استکهلم","سوئد","international"),
        ("اسلو","اسلو","نروژ","international"),
        ("کپنهاگ","کپنهاگ","دانمارک","international"),
        ("هلسینکی","هلسینکی","فنلاند","international"),
        ("مسکو","مسکو","روسیه","international"),
        ("سنت پترزبورگ","سنت پترزبورگ","روسیه","international"),
        ("پکن","پکن","چین","international"),
        ("شانگهای","شانگهای","چین","international"),
        ("توکیو","توکیو","ژاپن","international"),
        ("سئول","سئول","کره جنوبی","international"),
        ("دهلی","دهلی","هند","international"),
        ("بمبئی","بمبئی","هند","international"),
        ("بانکوک","بانکوک","تایلند","international"),
        ("پوکت","پوکت","تایلند","international"),
        ("کوالالامپور","کوالالامپور","مالزی","international"),
        ("سنگاپور","سنگاپور","سنگاپور","international"),
        ("جاکارتا","جاکارتا","اندونزی","international"),
        ("استراسبورگ","استراسبورگ","فرانسه","international"),
        ("لیون","لیون","فرانسه","international")
    ]

    for airport in airports:

        cursor.execute(
            """
            SELECT airport_id
            FROM airports
            WHERE airport_name=%s
            AND city=%s
            """,
            (airport[0], airport[1])
        )

        if not cursor.fetchone():

            cursor.execute(
                """
                INSERT INTO airports
                (
                    airport_name,
                    city,
                    country,
                    airport_type
                )
                VALUES(%s,%s,%s,%s)
                """,
                airport
            )

    db.commit()
    cursor.close()
    db.close()

# ===========================
# FLIGHTS
# ===========================

def create_table_flights():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights(
            flight_id INT AUTO_INCREMENT PRIMARY KEY,

            airline_id INT,

            origin_airport_id INT,
            destination_airport_id INT,

            flight_number VARCHAR(20) UNIQUE,

            flight_type ENUM('domestic','international'),

            departure_date DATE,
            departure_time TIME,
            arrival_time TIME,

            economy_capacity INT,
            business_capacity INT,

            economy_price DECIMAL(12,2),
            business_price DECIMAL(12,2),

            status ENUM(
                'available',
                'full',
                'cancelled'
            ) DEFAULT 'available',

            FOREIGN KEY (airline_id)
            REFERENCES airlines(airline_id),

            FOREIGN KEY (origin_airport_id)
            REFERENCES airports(airport_id),

            FOREIGN KEY (destination_airport_id)
            REFERENCES airports(airport_id)
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# RESERVATIONS
# ===========================

def create_table_reservations():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations(
            reservation_id INT AUTO_INCREMENT PRIMARY KEY,

            user_id INT,
            flight_id INT,

            reservation_code VARCHAR(30) UNIQUE,

            total_amount DECIMAL(12,2),

            status ENUM(
                'pending_payment',
                'pending_verification',
                'confirmed',
                'cancelled'
            ),

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(user_id),
                   
            FOREIGN KEY (flight_id)
            REFERENCES flights(flight_id)
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# PASSENGERS
# ===========================

def create_table_passengers():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers(
            passenger_id INT AUTO_INCREMENT PRIMARY KEY,

            reservation_id INT,

            passenger_type ENUM(
                'domestic',
                'international'
            ),

            first_name_fa VARCHAR(50),
            last_name_fa VARCHAR(50),

            first_name_en VARCHAR(50),
            last_name_en VARCHAR(50),

            national_code CHAR(10),
            passport_number VARCHAR(20),

            birth_date DATE,

            gender ENUM(
                'male',
                'female'
            ),

            FOREIGN KEY (reservation_id)
            REFERENCES reservations(reservation_id)
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# PAYMENTS
# ===========================

def create_table_payments():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            payment_id INT AUTO_INCREMENT PRIMARY KEY,

            reservation_id INT UNIQUE,

            receipt_file_id VARCHAR(255),

            amount DECIMAL(12,2),

            status ENUM(
                'pending',
                'verified',
                'rejected'
            ) DEFAULT 'pending',

            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (reservation_id)
            REFERENCES reservations(reservation_id)
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# TICKETS
# ===========================

def create_table_tickets():
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets(
            ticket_id INT AUTO_INCREMENT PRIMARY KEY,

            passenger_id INT UNIQUE,

            flight_id INT,

            seat_number VARCHAR(10),

            class_type ENUM(
                'economy',
                'business'
            ),

            ticket_code VARCHAR(50) UNIQUE,

            status ENUM(
                'issued',
                'cancelled'
            ) DEFAULT 'issued',

            issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (passenger_id)
            REFERENCES passengers(passenger_id),

            FOREIGN KEY (flight_id)
            REFERENCES flights(flight_id),

            UNIQUE(flight_id, seat_number)
        )
    """)

    db.commit()
    cursor.close()
    db.close()


# ===========================
# INIT DATABASE
# ===========================

def init_database():
    create_database()

    create_table_users()
    create_table_airlines()
    create_table_airports()
    create_table_flights()
    create_table_reservations()
    create_table_passengers()
    create_table_payments()
    create_table_tickets()


if __name__ == "__main__":
    init_database()
    print("IranFly Database Created Successfully")