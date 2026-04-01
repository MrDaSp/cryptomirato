// --- SUPABASE CONFIGURATION (Condivisa con BetMirato) ---
const SUPABASE_URL = 'https://kvwomwmnfrfohewadesg.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2d29td21uZnJmb2hld2FkZXNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2ODM1MDAsImV4cCI6MjA5MDI1OTUwMH0.26BXmGc3HMAmUO47FOYSk6EM6_t4j2qViLyoi1W8_S8';

// Lista email che godranno dei privilegi di Super Admin
const SUPER_ADMINS = ['admin@danitech.it', 'mrdasp@gmail.com']; // Sostituisci con la tua email reale

let sbClient;
let currentUser = null;
let currentSession = null;

// Inizializza il client connesso a Supabase
function initSupabase() {
    sbClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    sbClient.auth.onAuthStateChange((event, session) => {
        currentSession = session;
        currentUser = session?.user || null;
    });
}

// Funzione Registrazione
async function sbSignUp(email, password) {
    const { data, error } = await sbClient.auth.signUp({
        email: email, 
        password: password,
        options: { 
            emailRedirectTo: 'https://mrdasp.github.io/cryptomirato/index.html'
        }
    });
    if (error) throw error;
    return data;
}

// Funzione Login
async function sbSignIn(email, password) {
    const { data, error } = await sbClient.auth.signInWithPassword({ email: email, password: password });
    if (error) throw error;
    return data;
}

// Funzione Logout
async function sbSignOut() {
    const { error } = await sbClient.auth.signOut();
    if (error) throw error;
    currentUser = null;
    currentSession = null;
}

// Recupero Sessione Attiva
async function sbGetSession() {
    const { data, error } = await sbClient.auth.getSession();
    if (error) console.error("Session Error:", error);
    currentSession = data.session;
    currentUser = data.session?.user || null;
    return data.session;
}

// Utility: Verifica se l'utente corrente è un Super Admin
function isSuperAdmin() {
    if (!currentUser) return false;
    return SUPER_ADMINS.includes(currentUser.email);
}

// Utility: Ottieni una chiave per il LocalStorage univoca per questo utente
// In modo che un utente non veda il portafoglio dell'altro in caso di PC condiviso.
function getUserPortfolioKey() {
    if (!currentUser) return 'cryptomirato_portfolio_guest';
    return `cryptomirato_portfolio_${currentUser.id}`;
}
