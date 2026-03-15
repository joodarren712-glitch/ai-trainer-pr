import streamlit as st
from groq import Groq
from pypdf import PdfReader
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import hashlib

st.set_page_config(page_title="AI Employee Trainer", page_icon="🎓", layout="wide")

# --- AUTHENTICATION SETUP ---
def initialize_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'language' not in st.session_state:
        st.session_state.language = 'English'

initialize_auth()

# --- LANGUAGE SUPPORT ---
LANGUAGES = {
    'English': 'en',
    'Indonesian': 'id',
    'Chinese (Traditional)': 'zh-tw',
    'Chinese (Simplified)': 'zh-cn',
    'Spanish': 'es',
    'Arabic': 'ar',
    'German': 'de',
    'French': 'fr'
}

translations = {
    'English': {
        'app_title': 'AI Employee Trainer',
        'app_subtitle': 'Accelerated employee training using AI chat',
        'welcome_back': 'Welcome back',
        'register_title': 'Create Account',
        'register_subtitle': 'Complete the form below to get started',
        'full_name': 'Full Name',
        'email': 'Email Address',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'register_button': 'Create Account',
        'passwords_mismatch': 'Passwords do not match',
        'password_length': 'Password must be at least 6 characters long',
        'invalid_email': 'Please enter a valid email address',
        'fill_all_fields': 'Please fill in all fields',
        'email_exists': 'Email already registered',
        'registration_success': 'Registration successful! Welcome!',
        'search': 'Search',
        'search_placeholder': 'Search messages...',
        'not_found': 'Not found',
        'new_conversation': 'New Conversation',
        'conversations': 'Conversations',
        'edit_conversation_title': 'Edit Title',
        'appearance': 'Appearance',
        'choose_theme': 'Choose Theme',
        'language': 'Language',
        'profile': 'Profile',
        'name': 'Name',
        'logout': 'Logout',
        'training_mode': 'Training Mode',
        'select_mode': 'Select Training Mode',
        'knowledge_quiz': 'Knowledge Quiz',
        'roleplay_training': 'Roleplay Training',
        'roleplay_settings': 'Roleplay Settings',
        'company_type': 'Company Type',
        'scenario': 'Scenario',
        'difficulty_level': 'Difficulty Level',
        'start_roleplay': 'Start Roleplay',
        'score': 'Score',
        'send_score': 'Send Score',
        'sop': 'SOP Document',
        'upload_pdf': 'Upload PDF',
        'create_quiz': 'Create Quiz',
        'sop_uploaded': 'SOP successfully uploaded',
        'ask_question': 'Ask a training question or answer a quiz...',
        'end_roleplay_info': 'Type END ROLEPLAY to see performance evaluation',
        'edit_message': 'Edit message:',
        'save': 'Save',
        'cancel': 'Cancel',
        'sent_success': 'Sent successfully!',
        'fill_name_first': 'Fill name first!',
        'retail': 'Retail',
        'restaurant': 'Restaurant',
        'bank': 'Bank',
        'ecommerce': 'E-commerce',
        'hospitality': 'Hospitality',
        'healthcare': 'Healthcare',
        'technology': 'Technology',
        'upselling': 'Upselling',
        'complaint_handling': 'Complaint Handling',
        'problem_solving': 'Problem Solving',
        'customer_onboarding': 'Customer Onboarding',
        'technical_support': 'Technical Support',
        'angry_customer': 'Angry Customer',
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard',
        'auto': 'Auto',
        'light': 'Light',
        'dark': 'Dark',
        'excellent_correct': 'Excellent! That is correct.',
        'incorrect_info': 'Not quite right. Here is the correct information:',
        'performance_analysis': 'Performance Analysis',
        'conversation_title': 'Conversation',
        'enter_title': 'Enter conversation title',
        'settings': 'Settings',
        'quiz_mode': 'Quiz Mode',
        'roleplay_mode': 'Roleplay Mode',
        'type_message': 'Type your message...',
        'send': 'Send'
    },
    'Indonesian': {
        'app_title': 'AI Employee Trainer',
        'app_subtitle': 'Pelatihan karyawan yang dipercepat menggunakan obrolan AI',
        'welcome_back': 'Selamat datang kembali',
        'register_title': 'Buat Akun',
        'register_subtitle': 'Isi formulir di bawah untuk memulai',
        'full_name': 'Nama Lengkap',
        'email': 'Alamat Email',
        'password': 'Kata Sandi',
        'confirm_password': 'Konfirmasi Kata Sandi',
        'register_button': 'Buat Akun',
        'passwords_mismatch': 'Kata sandi tidak cocok',
        'password_length': 'Kata sandi harus minimal 6 karakter',
        'invalid_email': 'Masukkan alamat email yang valid',
        'fill_all_fields': 'Harap isi semua kolom',
        'email_exists': 'Email sudah terdaftar',
        'registration_success': 'Pendaftaran berhasil! Selamat datang!',
        'search': 'Cari',
        'search_placeholder': 'Cari pesan...',
        'not_found': 'Tidak ditemukan',
        'new_conversation': 'Percakapan Baru',
        'conversations': 'Percakapan',
        'edit_conversation_title': 'Edit Judul',
        'appearance': 'Tampilan',
        'choose_theme': 'Pilih Tema',
        'language': 'Bahasa',
        'profile': 'Profil',
        'name': 'Nama',
        'logout': 'Keluar',
        'training_mode': 'Mode Pelatihan',
        'select_mode': 'Pilih Mode Pelatihan',
        'knowledge_quiz': 'Kuis Pengetahuan',
        'roleplay_training': 'Latihan Peran',
        'roleplay_settings': 'Pengaturan Latihan Peran',
        'company_type': 'Jenis Perusahaan',
        'scenario': 'Skenario',
        'difficulty_level': 'Tingkat Kesulitan',
        'start_roleplay': 'Mulai Latihan Peran',
        'score': 'Nilai',
        'send_score': 'Kirim Nilai',
        'sop': 'Dokumen SOP',
        'upload_pdf': 'Unggah PDF',
        'create_quiz': 'Buat Kuis',
        'sop_uploaded': 'SOP berhasil diunggah',
        'ask_question': 'Tanyakan pertanyaan pelatihan atau jawab kuis...',
        'end_roleplay_info': 'Ketik END ROLEPLAY untuk melihat evaluasi kinerja',
        'edit_message': 'Edit pesan:',
        'save': 'Simpan',
        'cancel': 'Batal',
        'sent_success': 'Berhasil dikirim!',
        'fill_name_first': 'Isi nama terlebih dahulu!',
        'retail': 'Ritel',
        'restaurant': 'Restoran',
        'bank': 'Bank',
        'ecommerce': 'E-commerce',
        'hospitality': 'Perhotelan',
        'healthcare': 'Kesehatan',
        'technology': 'Teknologi',
        'upselling': 'Penjualan Tambahan',
        'complaint_handling': 'Penanganan Keluhan',
        'problem_solving': 'Pemecahan Masalah',
        'customer_onboarding': 'Onboarding Pelanggan',
        'technical_support': 'Dukungan Teknis',
        'angry_customer': 'Pelanggan Marah',
        'easy': 'Mudah',
        'medium': 'Sedang',
        'hard': 'Sulit',
        'auto': 'Otomatis',
        'light': 'Terang',
        'dark': 'Gelap',
        'excellent_correct': 'Sangat benar!',
        'incorrect_info': 'Kurang tepat. Berikut informasi yang benar:',
        'performance_analysis': 'Analisis Kinerja',
        'conversation_title': 'Percakapan',
        'enter_title': 'Masukkan judul percakapan',
        'settings': 'Pengaturan',
        'quiz_mode': 'Mode Kuis',
        'roleplay_mode': 'Mode Latihan Peran',
        'type_message': 'Ketik pesan Anda...',
        'send': 'Kirim'
    },
    'Chinese (Traditional)': {
        'app_title': 'AI 員工培訓系統',
        'app_subtitle': '使用 AI 聊天進行加速員工培訓',
        'welcome_back': '歡迎回來',
        'register_title': '建立帳戶',
        'register_subtitle': '填寫下方表格以開始使用',
        'full_name': '全名',
        'email': '電子郵件地址',
        'password': '密碼',
        'confirm_password': '確認密碼',
        'register_button': '建立帳戶',
        'passwords_mismatch': '密碼不相符',
        'password_length': '密碼必須至少 6 個字元',
        'invalid_email': '請輸入有效的電子郵件地址',
        'fill_all_fields': '請填寫所有欄位',
        'email_exists': '電子郵件已註冊',
        'registration_success': '註冊成功！歡迎！',
        'search': '搜尋',
        'search_placeholder': '搜尋訊息...',
        'not_found': '未找到',
        'new_conversation': '新對話',
        'conversations': '對話',
        'edit_conversation_title': '編輯標題',
        'appearance': '外觀',
        'choose_theme': '選擇主題',
        'language': '語言',
        'profile': '個人資料',
        'name': '姓名',
        'logout': '登出',
        'training_mode': '培訓模式',
        'select_mode': '選擇培訓模式',
        'knowledge_quiz': '知識測驗',
        'roleplay_training': '角色扮演培訓',
        'roleplay_settings': '角色扮演設定',
        'company_type': '公司類型',
        'scenario': '情境',
        'difficulty_level': '難度等級',
        'start_roleplay': '開始角色扮演',
        'score': '分數',
        'send_score': '發送分數',
        'sop': '標準作業程序文件',
        'upload_pdf': '上傳 PDF',
        'create_quiz': '建立測驗',
        'sop_uploaded': 'SOP 上傳成功',
        'ask_question': '詢問培訓問題或回答測驗...',
        'end_roleplay_info': '輸入 END ROLEPLAY 查看績效評估',
        'edit_message': '編輯訊息:',
        'save': '儲存',
        'cancel': '取消',
        'sent_success': '發送成功!',
        'fill_name_first': '請先填寫姓名!',
        'retail': '零售',
        'restaurant': '餐廳',
        'bank': '銀行',
        'ecommerce': '電子商務',
        'hospitality': '酒店業',
        'healthcare': '醫療保健',
        'technology': '科技',
        'upselling': '追加銷售',
        'complaint_handling': '投訴處理',
        'problem_solving': '問題解決',
        'customer_onboarding': '客戶引導',
        'technical_support': '技術支援',
        'angry_customer': '憤怒的客戶',
        'easy': '簡單',
        'medium': '中等',
        'hard': '困難',
        'auto': '自動',
        'light': '明亮',
        'dark': '深色',
        'excellent_correct': '太好了！這是正確的。',
        'incorrect_info': '不太正確。這是正確的資訊:',
        'performance_analysis': '績效分析',
        'conversation_title': '對話',
        'enter_title': '輸入對話標題',
        'settings': '設定',
        'quiz_mode': '測驗模式',
        'roleplay_mode': '角色扮演模式',
        'type_message': '輸入您的訊息...',
        'send': '發送'
    },
    'Chinese (Simplified)': {
        'app_title': 'AI 员工培训系统',
        'app_subtitle': '使用 AI 聊天进行加速员工培训',
        'welcome_back': '欢迎回来',
        'register_title': '创建账户',
        'register_subtitle': '填写下方表格以开始使用',
        'full_name': '全名',
        'email': '电子邮件地址',
        'password': '密码',
        'confirm_password': '确认密码',
        'register_button': '创建账户',
        'passwords_mismatch': '密码不匹配',
        'password_length': '密码必须至少 6 个字符',
        'invalid_email': '请输入有效的电子邮件地址',
        'fill_all_fields': '请填写所有字段',
        'email_exists': '电子邮件已注册',
        'registration_success': '注册成功！欢迎！',
        'search': '搜索',
        'search_placeholder': '搜索消息...',
        'not_found': '未找到',
        'new_conversation': '新对话',
        'conversations': '对话',
        'edit_conversation_title': '编辑标题',
        'appearance': '外观',
        'choose_theme': '选择主题',
        'language': '语言',
        'profile': '个人资料',
        'name': '姓名',
        'logout': '登出',
        'training_mode': '培训模式',
        'select_mode': '选择培训模式',
        'knowledge_quiz': '知识测验',
        'roleplay_training': '角色扮演培训',
        'roleplay_settings': '角色扮演设置',
        'company_type': '公司类型',
        'scenario': '情境',
        'difficulty_level': '难度等级',
        'start_roleplay': '开始角色扮演',
        'score': '分数',
        'send_score': '发送分数',
        'sop': '标准作业程序文档',
        'upload_pdf': '上传 PDF',
        'create_quiz': '创建测验',
        'sop_uploaded': 'SOP 上传成功',
        'ask_question': '询问培训问题或回答测验...',
        'end_roleplay_info': '输入 END ROLEPLAY 查看绩效评估',
        'edit_message': '编辑消息:',
        'save': '保存',
        'cancel': '取消',
        'sent_success': '发送成功!',
        'fill_name_first': '请先填写姓名!',
        'retail': '零售',
        'restaurant': '餐厅',
        'bank': '银行',
        'ecommerce': '电子商务',
        'hospitality': '酒店业',
        'healthcare': '医疗保健',
        'technology': '科技',
        'upselling': '追加销售',
        'complaint_handling': '投诉处理',
        'problem_solving': '问题解决',
        'customer_onboarding': '客户引导',
        'technical_support': '技术支持',
        'angry_customer': '愤怒的客户',
        'easy': '简单',
        'medium': '中等',
        'hard': '困难',
        'auto': '自动',
        'light': '明亮',
        'dark': '深色',
        'excellent_correct': '太好了！这是正确的。',
        'incorrect_info': '不太正确。这是正确的信息:',
        'performance_analysis': '绩效分析',
        'conversation_title': '对话',
        'enter_title': '输入对话标题',
        'settings': '设置',
        'quiz_mode': '测验模式',
        'roleplay_mode': '角色扮演模式',
        'type_message': '输入您的消息...',
        'send': '发送'
    },
    'Spanish': {
        'app_title': 'AI Employee Trainer',
        'app_subtitle': 'Capacitación acelerada de empleados usando chat AI',
        'welcome_back': 'Bienvenido de nuevo',
        'register_title': 'Crear Cuenta',
        'register_subtitle': 'Complete el formulario a continuación para comenzar',
        'full_name': 'Nombre Completo',
        'email': 'Correo Electrónico',
        'password': 'Contraseña',
        'confirm_password': 'Confirmar Contraseña',
        'register_button': 'Crear Cuenta',
        'passwords_mismatch': 'Las contraseñas no coinciden',
        'password_length': 'La contraseña debe tener al menos 6 caracteres',
        'invalid_email': 'Por favor ingrese un correo electrónico válido',
        'fill_all_fields': 'Por favor complete todos los campos',
        'email_exists': 'Correo electrónico ya registrado',
        'registration_success': '¡Registro exitoso! ¡Bienvenido!',
        'search': 'Buscar',
        'search_placeholder': 'Buscar mensajes...',
        'not_found': 'No encontrado',
        'new_conversation': 'Nueva Conversación',
        'conversations': 'Conversaciones',
        'edit_conversation_title': 'Editar Título',
        'appearance': 'Apariencia',
        'choose_theme': 'Elegir Tema',
        'language': 'Idioma',
        'profile': 'Perfil',
        'name': 'Nombre',
        'logout': 'Cerrar Sesión',
        'training_mode': 'Modo de Entrenamiento',
        'select_mode': 'Seleccionar Modo de Entrenamiento',
        'knowledge_quiz': 'Cuestionario de Conocimiento',
        'roleplay_training': 'Entrenamiento de Role Play',
        'roleplay_settings': 'Configuración de Role Play',
        'company_type': 'Tipo de Empresa',
        'scenario': 'Escenario',
        'difficulty_level': 'Nivel de Dificultad',
        'start_roleplay': 'Iniciar Role Play',
        'score': 'Puntuación',
        'send_score': 'Enviar Puntuación',
        'sop': 'Documento SOP',
        'upload_pdf': 'Subir PDF',
        'create_quiz': 'Crear Cuestionario',
        'sop_uploaded': 'SOP subido con éxito',
        'ask_question': 'Haga una pregunta de entrenamiento o responda un cuestionario...',
        'end_roleplay_info': 'Escriba END ROLEPLAY para ver la evaluación del desempeño',
        'edit_message': 'Editar mensaje:',
        'save': 'Guardar',
        'cancel': 'Cancelar',
        'sent_success': '¡Enviado con éxito!',
        'fill_name_first': '¡Complete el nombre primero!',
        'retail': 'Minorista',
        'restaurant': 'Restaurante',
        'bank': 'Banco',
        'ecommerce': 'Comercio Electrónico',
        'hospitality': 'Hospitalidad',
        'healthcare': 'Atención Médica',
        'technology': 'Tecnología',
        'upselling': 'Venta Adicional',
        'complaint_handling': 'Manejo de Reclamaciones',
        'problem_solving': 'Resolución de Problemas',
        'customer_onboarding': 'Integración de Clientes',
        'technical_support': 'Soporte Técnico',
        'angry_customer': 'Cliente Molesto',
        'easy': 'Fácil',
        'medium': 'Medio',
        'hard': 'Difícil',
        'auto': 'Automático',
        'light': 'Claro',
        'dark': 'Oscuro',
        'excellent_correct': '¡Excelente! Esa es la respuesta correcta.',
        'incorrect_info': 'No del todo correcto. Aquí está la información correcta:',
        'performance_analysis': 'Análisis de Desempeño',
        'conversation_title': 'Conversación',
        'enter_title': 'Ingrese el título de la conversación',
        'settings': 'Configuración',
        'quiz_mode': 'Modo Cuestionario',
        'roleplay_mode': 'Modo Role Play',
        'type_message': 'Escriba su mensaje...',
        'send': 'Enviar'
    },
    'Arabic': {
        'app_title': 'مدرب الموظفين بالذكاء الاصطناعي',
        'app_subtitle': 'تدريب متسارع للموظفين باستخدام الدردشة بالذكاء الاصطناعي',
        'welcome_back': 'مرحباً بعودتك',
        'register_title': 'إنشاء حساب',
        'register_subtitle': 'أكمل النموذج أدناه للبدء',
        'full_name': 'الاسم الكامل',
        'email': 'عنوان البريد الإلكتروني',
        'password': 'كلمة المرور',
        'confirm_password': 'تأكيد كلمة المرور',
        'register_button': 'إنشاء حساب',
        'passwords_mismatch': 'كلمات المرور غير متطابقة',
        'password_length': 'يجب أن تكون كلمة المرور 6 أحرف على الأقل',
        'invalid_email': 'يرجى إدخال عنوان بريد إلكتروني صالح',
        'fill_all_fields': 'يرجى ملء جميع الحقول',
        'email_exists': 'البريد الإلكتروني مسجل بالفعل',
        'registration_success': 'تم التسجيل بنجاح! مرحباً!',
        'search': 'بحث',
        'search_placeholder': 'بحث في الرسائل...',
        'not_found': 'غير موجود',
        'new_conversation': 'محادثة جديدة',
        'conversations': 'المحادثات',
        'edit_conversation_title': 'تعديل العنوان',
        'appearance': 'المظهر',
        'choose_theme': 'اختر السمة',
        'language': 'اللغة',
        'profile': 'الملف الشخصي',
        'name': 'الاسم',
        'logout': 'تسجيل خروج',
        'training_mode': 'وضع التدريب',
        'select_mode': 'اختر وضع التدريب',
        'knowledge_quiz': 'اختبار المعرفة',
        'roleplay_training': 'تدريب لعب الأدوار',
        'roleplay_settings': 'إعدادات لعب الأدوار',
        'company_type': 'نوع الشركة',
        'scenario': 'السيناريو',
        'difficulty_level': 'مستوى الصعوبة',
        'start_roleplay': 'بدء لعب الأدوار',
        'score': 'النقاط',
        'send_score': 'إرسال النقاط',
        'sop': 'وثيقة إجراءات التشغيل القياسية',
        'upload_pdf': 'تحميل PDF',
        'create_quiz': 'إنشاء اختبار',
        'sop_uploaded': 'تم تحميل إجراءات التشغيل القياسية بنجاح',
        'ask_question': 'اطرح سؤال تدريب أو أجب على اختبار...',
        'end_roleplay_info': 'اكتب END ROLEPLAY لرؤية تقييم الأداء',
        'edit_message': 'تعديل الرسالة:',
        'save': 'حفظ',
        'cancel': 'إلغاء',
        'sent_success': 'تم الإرسال بنجاح!',
        'fill_name_first': 'املأ الاسم أولاً!',
        'retail': 'تجزئة',
        'restaurant': 'مطعم',
        'bank': 'بنك',
        'ecommerce': 'تجارة إلكترونية',
        'hospitality': 'ضيافة',
        'healthcare': 'رعاية صحية',
        'technology': 'تكنولوجيا',
        'upselling': 'بيع إضافي',
        'complaint_handling': 'معالجة الشكاوى',
        'problem_solving': 'حل المشكلات',
        'customer_onboarding': 'دمج العملاء',
        'technical_support': 'دعم فني',
        'angry_customer': 'عميل غاضب',
        'easy': 'سهل',
        'medium': 'متوسط',
        'hard': 'صعب',
        'auto': 'تلقائي',
        'light': 'فاتح',
        'dark': 'داكن',
        'excellent_correct': 'ممتاز! هذه إجابة صحيحة.',
        'incorrect_info': 'ليس صحيحاً تماماً. إليك المعلومات الصحيحة:',
        'performance_analysis': 'تحليل الأداء',
        'conversation_title': 'محادثة',
        'enter_title': 'أدخل عنوان المحادثة',
        'settings': 'الإعدادات',
        'quiz_mode': 'وضع الاختبار',
        'roleplay_mode': 'وضع لعب الأدوار',
        'type_message': 'اكتب رسالتك...',
        'send': 'إرسال'
    },
    'German': {
        'app_title': 'AI Mitarbeiter-Trainer',
        'app_subtitle': 'Beschleunigte Mitarbeiterschulung mit AI-Chat',
        'welcome_back': 'Willkommen zurück',
        'register_title': 'Konto Erstellen',
        'register_subtitle': 'Füllen Sie das untenstehende Formular aus, um zu beginnen',
        'full_name': 'Vollständiger Name',
        'email': 'E-Mail-Adresse',
        'password': 'Passwort',
        'confirm_password': 'Passwort Bestätigen',
        'register_button': 'Konto Erstellen',
        'passwords_mismatch': 'Passwörter stimmen nicht überein',
        'password_length': 'Passwort muss mindestens 6 Zeichen lang sein',
        'invalid_email': 'Bitte geben Sie eine gültige E-Mail-Adresse ein',
        'fill_all_fields': 'Bitte füllen Sie alle Felder aus',
        'email_exists': 'E-Mail bereits registriert',
        'registration_success': 'Registrierung erfolgreich! Willkommen!',
        'search': 'Suchen',
        'search_placeholder': 'Nachrichten suchen...',
        'not_found': 'Nicht gefunden',
        'new_conversation': 'Neue Konversation',
        'conversations': 'Konversationen',
        'edit_conversation_title': 'Titel Bearbeiten',
        'appearance': 'Erscheinungsbild',
        'choose_theme': 'Thema Wählen',
        'language': 'Sprache',
        'profile': 'Profil',
        'name': 'Name',
        'logout': 'Abmelden',
        'training_mode': 'Trainingsmodus',
        'select_mode': 'Trainingsmodus Auswählen',
        'knowledge_quiz': 'Wissensquiz',
        'roleplay_training': 'Rollenspiel-Training',
        'roleplay_settings': 'Rollenspiel-Einstellungen',
        'company_type': 'Unternehmenstyp',
        'scenario': 'Szenario',
        'difficulty_level': 'Schwierigkeitsgrad',
        'start_roleplay': 'Rollenspiel Starten',
        'score': 'Punktzahl',
        'send_score': 'Punktzahl Senden',
        'sop': 'SOP-Dokument',
        'upload_pdf': 'PDF Hochladen',
        'create_quiz': 'Quiz Erstellen',
        'sop_uploaded': 'SOP erfolgreich hochgeladen',
        'ask_question': 'Stellen Sie eine Trainingsfrage oder beantworten Sie ein Quiz...',
        'end_roleplay_info': 'Geben Sie END ROLEPLAY ein, um die Leistungsbewertung zu sehen',
        'edit_message': 'Nachricht bearbeiten:',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'sent_success': 'Erfolgreich gesendet!',
        'fill_name_first': 'Name zuerst ausfüllen!',
        'retail': 'Einzelhandel',
        'restaurant': 'Restaurant',
        'bank': 'Bank',
        'ecommerce': 'E-Commerce',
        'hospitality': 'Gastgewerbe',
        'healthcare': 'Gesundheitswesen',
        'technology': 'Technologie',
        'upselling': 'Verkaufssteigerung',
        'complaint_handling': 'Beschwerdemanagement',
        'problem_solving': 'Problemlösung',
        'customer_onboarding': 'Kunden-Onboarding',
        'technical_support': 'Technischer Support',
        'angry_customer': 'Verärgerter Kunde',
        'easy': 'Einfach',
        'medium': 'Mittel',
        'hard': 'Schwer',
        'auto': 'Automatisch',
        'light': 'Hell',
        'dark': 'Dunkel',
        'excellent_correct': 'Ausgezeichnet! Das ist korrekt.',
        'incorrect_info': 'Nicht ganz richtig. Hier sind die korrekten Informationen:',
        'performance_analysis': 'Leistungsanalyse',
        'conversation_title': 'Konversation',
        'enter_title': 'Geben Sie den Konversationstitel ein',
        'settings': 'Einstellungen',
        'quiz_mode': 'Quiz-Modus',
        'roleplay_mode': 'Rollenspiel-Modus',
        'type_message': 'Nachricht eingeben...',
        'send': 'Senden'
    },
    'French': {
        'app_title': 'AI Employee Trainer',
        'app_subtitle': 'Formation accélérée des employés utilisant le chat AI',
        'welcome_back': 'Bon retour',
        'register_title': 'Créer un Compte',
        'register_subtitle': 'Remplissez le formulaire ci-dessous pour commencer',
        'full_name': 'Nom Complet',
        'email': 'Adresse E-mail',
        'password': 'Mot de Passe',
        'confirm_password': 'Confirmer le Mot de Passe',
        'register_button': 'Créer un Compte',
        'passwords_mismatch': 'Les mots de passe ne correspondent pas',
        'password_length': 'Le mot de passe doit contenir au moins 6 caractères',
        'invalid_email': 'Veuillez entrer une adresse e-mail valide',
        'fill_all_fields': 'Veuillez remplir tous les champs',
        'email_exists': 'E-mail déjà enregistré',
        'registration_success': 'Inscription réussie! Bienvenue!',
        'search': 'Rechercher',
        'search_placeholder': 'Rechercher des messages...',
        'not_found': 'Non trouvé',
        'new_conversation': 'Nouvelle Conversation',
        'conversations': 'Conversations',
        'edit_conversation_title': 'Modifier le Titre',
        'appearance': 'Apparence',
        'choose_theme': 'Choisir le Thème',
        'language': 'Langue',
        'profile': 'Profil',
        'name': 'Nom',
        'logout': 'Déconnexion',
        'training_mode': 'Mode Formation',
        'select_mode': 'Sélectionner le Mode Formation',
        'knowledge_quiz': 'Quiz de Connaissances',
        'roleplay_training': 'Formation par Jeu de Rôle',
        'roleplay_settings': 'Paramètres de Jeu de Rôle',
        'company_type': 'Type d\'Entreprise',
        'scenario': 'Scénario',
        'difficulty_level': 'Niveau de Difficulté',
        'start_roleplay': 'Démarrer le Jeu de Rôle',
        'score': 'Score',
        'send_score': 'Envoyer le Score',
        'sop': 'Document SOP',
        'upload_pdf': 'Télécharger PDF',
        'create_quiz': 'Créer un Quiz',
        'sop_uploaded': 'SOP téléchargé avec succès',
        'ask_question': 'Posez une question de formation ou répondez à un quiz...',
        'end_roleplay_info': 'Tapez END ROLEPLAY pour voir l\'évaluation des performances',
        'edit_message': 'Modifier le message:',
        'save': 'Enregistrer',
        'cancel': 'Annuler',
        'sent_success': 'Envoyé avec succès!',
        'fill_name_first': 'Remplissez le nom d\'abord!',
        'retail': 'Commerce de Détail',
        'restaurant': 'Restaurant',
        'bank': 'Banque',
        'ecommerce': 'Commerce Électronique',
        'hospitality': 'Hôtellerie',
        'healthcare': 'Soins de Santé',
        'technology': 'Technologie',
        'upselling': 'Vente Additionnelle',
        'complaint_handling': 'Gestion des Réclamations',
        'problem_solving': 'Résolution de Problèmes',
        'customer_onboarding': 'Intégration Client',
        'technical_support': 'Support Technique',
        'angry_customer': 'Client Mécontent',
        'easy': 'Facile',
        'medium': 'Moyen',
        'hard': 'Difficile',
        'auto': 'Automatique',
        'light': 'Clair',
        'dark': 'Sombre',
        'excellent_correct': 'Excellent! C\'est la bonne réponse.',
        'incorrect_info': 'Pas tout à fait correct. Voici l\'information correcte:',
        'performance_analysis': 'Analyse des Performances',
        'conversation_title': 'Conversation',
        'enter_title': 'Entrez le titre de la conversation',
        'settings': 'Paramètres',
        'quiz_mode': 'Mode Quiz',
        'roleplay_mode': 'Mode Jeu de Rôle',
        'type_message': 'Tapez votre message...',
        'send': 'Envoyer'
    }
}

# Get current language translations
lang = translations[st.session_state.language]

# --- API ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- AUTHENTICATION FUNCTIONS ---
def register_user(name, email, password):
    """Register a new user."""
    try:
        user_data = st.secrets.get("users", {})
        if email in user_data:
            return False
        else:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return True
    except:
        return True

def login_page():
    """Display the registration page."""
    # Center the registration form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 8px;">{lang['app_title']}</h1>
            <p style="color: var(--text-secondary); font-size: 1.1rem;">{lang['app_subtitle']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"### {lang['register_title']}")
        st.caption(lang['register_subtitle'])
        
        with st.form("registration_form"):
            name = st.text_input(lang['full_name'], placeholder="John Doe")
            email = st.text_input(lang['email'], placeholder="john@example.com")
            password = st.text_input(lang['password'], type="password", placeholder="••••••••")
            confirm_password = st.text_input(lang['confirm_password'], type="password", placeholder="••••••••")
            submitted = st.form_submit_button(lang['register_button'], use_container_width=True)

            if submitted:
                if name and email and password and confirm_password:
                    if password != confirm_password:
                        st.error(lang['passwords_mismatch'])
                    elif len(password) < 6:
                        st.error(lang['password_length'])
                    elif "@" not in email or "." not in email:
                        st.error(lang['invalid_email'])
                    else:
                        if register_user(name, email, password):
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.user_name = name
                            st.success(lang['registration_success'])
                            st.rerun()
                        else:
                            st.error(lang['email_exists'])
                else:
                    st.warning(lang['fill_all_fields'])

# Check if user is logged in, if not show login page
if not st.session_state.logged_in:
    login_page()
    st.stop()

# --- SESSION STATE ---
if "sop_teks" not in st.session_state:
    st.session_state.sop_teks = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "skor" not in st.session_state:
    st.session_state.skor = 0

if "mode" not in st.session_state:
    st.session_state.mode = "quiz"

if "roleplay_active" not in st.session_state:
    st.session_state.roleplay_active = False

if "scenario" not in st.session_state:
    st.session_state.scenario = "Angry Customer"

if "level" not in st.session_state:
    st.session_state.level = "easy"

if "company_type" not in st.session_state:
    st.session_state.company_type = "Retail"

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 1

if "theme" not in st.session_state:
    st.session_state.theme = "auto"

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if "edit_title_chat_id" not in st.session_state:
    st.session_state.edit_title_chat_id = None

# --- AI FUNCTION ---
def panggil_ai(teks_input, konteks_sop):
    chat_id = st.session_state.current_chat_id
    chat_list = st.session_state.all_chats[chat_id]

    if not chat_list or chat_list[-1]["content"] != teks_input:
        chat_list.append({
            "role": "user",
            "content": teks_input
        })

    if st.session_state.mode == "roleplay":
        st.session_state.conversation_history.append({
            "role": "user",
            "content": teks_input
        })

        if "END ROLEPLAY" in teks_input.upper():
            prompt = f"""
            You are an AI Trainer.
            Analyze this conversation:
            {st.session_state.conversation_history}
            Give score (0-100) for Communication, Empathy, Problem Solving, Persuasion.
            Provide: 1) Strength 2) Mistakes 3) Better answer example 4) Tips
            """
        else:
            prompt = f"""
            You are a CUSTOMER.
            Company: {st.session_state.company_type}
            Scenario: {st.session_state.scenario}
            Level: {st.session_state.level}
            Act like human, show emotion, no explanation, stay in role.
            Conversation: {st.session_state.conversation_history}
            """
    else:
        prompt = f"""
        You are an AI Corporate Training Assistant.
        Training Material: {konteks_sop}
        Create quiz questions if requested.
        If answer correct: 'Excellent! That is correct.'
        If incorrect: 'Not quite right. Here is the correct information:'
        Provide detailed explanations.
        """

    riwayat = [{"role": "system", "content": prompt}]
    for m in st.session_state.all_chats[st.session_state.current_chat_id]:
        riwayat.append(m)

    response = client.chat.completions.create(
        messages=riwayat,
        model="llama-3.3-70b-versatile"
    )

    hasil = response.choices[0].message.content

    st.session_state.all_chats[st.session_state.current_chat_id].append({
        "role": "assistant",
        "content": hasil
    })

    if st.session_state.mode == "roleplay":
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": hasil
        })

    if "Excellent! That is correct." in hasil:
        st.session_state.skor += 1

def regenerate_from_index(edit_index):
    chat_id = st.session_state.current_chat_id
    chat_history = st.session_state.all_chats[chat_id]
    new_history = chat_history[:edit_index + 1]
    st.session_state.all_chats[chat_id] = new_history

    if st.session_state.mode == "roleplay":
        st.session_state.conversation_history = []
        for msg in new_history:
            st.session_state.conversation_history.append(msg)

    last_user_message = new_history[-1]["content"]
    panggil_ai(last_user_message, st.session_state.sop_teks)

# --- MAIN APP LAYOUT ---
# Header
col_logo, col_title, col_user = st.columns([0.5, 2, 1])
with col_logo:
    st.markdown("### 🎓")
with col_title:
    st.markdown(f"# {lang['app_title']}")
    st.caption(lang['app_subtitle'])
with col_user:
    if st.session_state.user_name:
        st.write(f"**{lang['welcome_back']}, {st.session_state.user_name}**")

st.divider()

# Main content area with sidebar
main_col, sidebar_col = st.columns([3, 1])

with main_col:
    # Mode indicator
    mode_badge = lang['quiz_mode'] if st.session_state.mode == "quiz" else lang['roleplay_mode']
    st.write(f"**{mode_badge}**")

    if st.session_state.mode == "roleplay":
        st.info(lang['end_roleplay_info'])

    chat = st.session_state.all_chats.get(st.session_state.current_chat_id, [])

    for i, msg in enumerate(chat):
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            if st.session_state.get("edit_index") == i:
                new_text = st.text_area(lang['edit_message'], value=content, key=f"edit_{i}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(lang['save'], key=f"save_{i}"):
                        chat[i]["content"] = new_text
                        st.session_state.edit_index = None
                        regenerate_from_index(i)
                        st.rerun()
                with col2:
                    if st.button(lang['cancel'], key=f"cancel_{i}"):
                        st.session_state.edit_index = None
                        st.rerun()
            else:
                st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(content)

        if role == "user" and st.session_state.get("edit_index") != i:
            if st.button("Edit", key=f"floating_edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()

    # Chat input
    prompt = st.chat_input(lang['type_message'])

    if prompt:
        if st.session_state.mode == "roleplay":
            panggil_ai(prompt, st.session_state.sop_teks)
            st.rerun()
        else:
            if st.session_state.sop_teks:
                panggil_ai(prompt, st.session_state.sop_teks)
                st.rerun()
            else:
                st.warning(lang['fill_name_first'])

with sidebar_col:
    st.markdown("### Search")
    search_query = st.text_input(lang['search_placeholder'], key="search_box", label_visibility="collapsed")

    results = []
    if search_query:
        for chat_id, messages in st.session_state.all_chats.items():
            for m in messages:
                if search_query.lower() in m["content"].lower():
                    results.append((chat_id, m["content"]))

        if results:
            for chat_id, text in results:
                st.write(f"- {chat_id}: {text[:50]}...")
        else:
            st.write(lang['not_found'])

    st.divider()

    if st.button(lang['new_conversation'], use_container_width=True):
        st.session_state.chat_counter += 1
        new_chat_id = f"chat_{st.session_state.chat_counter}"
        st.session_state.current_chat_id = new_chat_id
        st.session_state.all_chats[new_chat_id] = []
        st.session_state.chat_titles[new_chat_id] = f"{lang['conversation_title']} {st.session_state.chat_counter}"
        st.rerun()

    st.markdown(f"### {lang['conversations']}")

    for chat_id in st.session_state.all_chats.keys():
        title = st.session_state.chat_titles.get(chat_id, chat_id)

        if st.session_state.get("edit_title_chat_id") == chat_id:
            new_title = st.text_input(lang['edit_conversation_title'], value=title, key=f"title_edit_{chat_id}", label_visibility="collapsed")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(lang['save'], key=f"save_title_{chat_id}"):
                    st.session_state.chat_titles[chat_id] = new_title
                    st.session_state.edit_title_chat_id = None
                    st.rerun()
            with col2:
                if st.button(lang['cancel'], key=f"cancel_title_{chat_id}"):
                    st.session_state.edit_title_chat_id = None
                    st.rerun()
        else:
            btn = st.button(title, key=f"chat_{chat_id}", use_container_width=True)
            if btn:
                st.session_state.current_chat_id = chat_id
                st.rerun()

            if st.button(f"{lang['edit_conversation_title']}", key=f"edit_btn_{chat_id}", use_container_width=True):
                st.session_state.edit_title_chat_id = chat_id
                st.rerun()

    st.divider()

    st.markdown(f"### {lang['settings']}")

    theme_option = st.selectbox(lang['choose_theme'], [lang['auto'], lang['light'], lang['dark']])

    if theme_option == lang['light']:
        st.session_state.theme = "light"
    elif theme_option == lang['dark']:
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "auto"

    selected_language = st.selectbox(lang['language'], list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.language))
    st.session_state.language = selected_language
    lang = translations[st.session_state.language]

    st.divider()

    st.markdown(f"### {lang['profile']}")

    if st.session_state.user_email:
        st.write(f"**{st.session_state.user_name}**")
        st.write(st.session_state.user_email)

        st.text_input(lang['name'], value=st.session_state.user_name, key="profile_name")

        if st.button(lang['logout'], use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.rerun()

    st.divider()

    st.markdown(f"### {lang['training_mode']}")

    mode = st.selectbox(lang['select_mode'], [lang['knowledge_quiz'], lang['roleplay_training']])

    if mode == lang['roleplay_training']:
        st.session_state.mode = "roleplay"
    else:
        st.session_state.mode = "quiz"

    if st.session_state.mode == "roleplay":
        st.markdown(f"#### {lang['roleplay_settings']}")

        st.session_state.company_type = st.selectbox(lang['company_type'],
            [lang['retail'], lang['restaurant'], lang['bank'], lang['ecommerce'], lang['hospitality'], lang['healthcare'], lang['technology']])

        st.session_state.scenario = st.selectbox(lang['scenario'],
            [lang['angry_customer'], lang['upselling'], lang['complaint_handling'], lang['problem_solving'], lang['customer_onboarding'], lang['technical_support']])

        st.session_state.level = st.selectbox(lang['difficulty_level'], [lang['easy'], lang['medium'], lang['hard']])

        if st.button(lang['start_roleplay'], use_container_width=True):
            st.session_state.roleplay_active = True
            st.session_state.conversation_history = []
            panggil_ai("START ROLEPLAY", st.session_state.sop_teks)
            st.rerun()

    st.divider()
    st.metric(lang['score'], st.session_state.skor)

    st.divider()

    st.markdown(f"### {lang['sop']}")
    uploaded_file = st.file_uploader(lang['upload_pdf'], type="pdf")

    if uploaded_file:
        sop_teks = ""
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            sop_teks += page.extract_text()

        st.session_state.sop_teks = sop_teks
        st.success(lang['sop_uploaded'])

        if st.button(lang['create_quiz'], use_container_width=True):
            panggil_ai("Create 1 multiple choice question about the training material", st.session_state.sop_teks)
            st.rerun()

# Score sending
if st.session_state.user_name and st.session_state.skor > 0:
    if st.button(lang['send_score']):
        df_baru = pd.DataFrame({
            lang['name']: [st.session_state.user_name],
            lang['score']: [st.session_state.skor],
            "Tanggal": [datetime.now()]
        })

        url = st.secrets["connections"]["gsheets"]["spreadsheet"]

        try:
            df_lama = conn.read(spreadsheet=url, worksheet="Sheet1")
        except:
            df_lama = pd.DataFrame()

        df = pd.concat([df_lama, df_baru])
        conn.update(spreadsheet=url, worksheet="Sheet1", data=df)

        st.success(lang['sent_success'])
        st.balloons()
