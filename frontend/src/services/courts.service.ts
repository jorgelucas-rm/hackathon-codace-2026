// Service de quadras — por enquanto retorna dados mockados.
// Quando o backend estiver pronto, basta trocar as funções por chamadas fetch("/api/courts...").

export interface CourtSlot {
    time: string;
    status: "disponivel" | "reservado" | "privada" | "ultimas" | "indisponivel";
    spots: number;
}

export interface CourtReview {
    name: string;
    initials: string;
    rating: number;
    text: string;
    date: string;
}

export interface Court {
    id: number;
    name: string;
    address: string;
    neighborhood: string;
    sports: string[];
    sportTags: string[];
    rating: number;
    reviewCount: number;
    distance: string;
    price: string;
    premium: boolean;
    gradient: string;
    desc: string;
    amenities: string[];
    todaySlots: CourtSlot[];
    reviews: CourtReview[];
}

export interface TimeSlot {
    time: string;
    price: string;
    duration: string;
    spots: number;
    status: CourtSlot["status"];
}

export interface DayOption {
    label: string;
    date: string;
}

const FORTALEZA_COURTS: Court[] = [
    {
        id: 1,
        name: "Arena Beira-Mar",
        address: "Av. Beira-Mar, 2800 · Meireles",
        neighborhood: "Praia de Iracema, Fortaleza",
        sports: ["Beach Tennis", "Vôlei"],
        sportTags: ["Beach Tennis", "Vôlei"],
        rating: 4.8, reviewCount: 128,
        distance: "1.2 km", price: "R$ 90/h",
        premium: true,
        gradient: "linear-gradient(135deg, rgba(173,153,0,0.2), #E8D7BD)",
        desc: "Quadra de beach tênis com areia importada e iluminação profissional, a 200m da praia. Ideal para jogos noturnos.",
        amenities: ["Estacionamento", "Vestiário", "Bar/Lanchonete", "Wi-Fi"],
        todaySlots: [
            { time: "18:00", status: "privada", spots: 0 },
            { time: "19:00", status: "disponivel", spots: 7 },
            { time: "20:00", status: "privada", spots: 0 },
            { time: "21:00", status: "disponivel", spots: 2 },
        ],
        reviews: [
            { name: "Marina O.", initials: "MO", rating: 5, text: "Quadra muito bem cuidada, iluminação ótima à noite. Voltarei sempre!", date: "há 2 dias" },
            { name: "Diego R.", initials: "DR", rating: 4, text: "Preço justo, atendimento excelente! Só falta mais estacionamento.", date: "há 5 dias" },
            { name: "Ana C.", initials: "AC", rating: 5, text: "Melhor quadra de beach tênis de Fortaleza! Areia de qualidade.", date: "há 1 semana" },
            { name: "Lucas M.", initials: "LM", rating: 4, text: "Ótima estrutura, vestiários limpos e bar no local.", date: "há 2 semanas" },
        ],
    },
    {
        id: 2,
        name: "Arena Prime Futebol",
        address: "Av. Santos Dumont, 5532 · Aldeota",
        neighborhood: "Aldeota, Fortaleza",
        sports: ["Futebol Society", "Futsal"],
        sportTags: ["Society", "Futsal"],
        rating: 4.7, reviewCount: 214,
        distance: "2.3 km", price: "R$ 120/h",
        premium: true,
        gradient: "linear-gradient(135deg, rgba(47,175,160,0.15), #E8D7BD)",
        desc: "Arena de futebol society com grama sintética de última geração. 6 quadras, iluminação LED e câmeras de segurança.",
        amenities: ["Estacionamento", "Vestiário", "Lanchonete", "Wi-Fi"],
        todaySlots: [
            { time: "17:00", status: "disponivel", spots: 4 },
            { time: "18:00", status: "disponivel", spots: 4 },
            { time: "19:00", status: "reservado", spots: 0 },
            { time: "20:00", status: "disponivel", spots: 3 },
        ],
        reviews: [
            { name: "Pedro A.", initials: "PA", rating: 5, text: "Melhor arena de Fortaleza! Grama excelente, vestiários ótimos.", date: "há 1 dia" },
            { name: "Rafael S.", initials: "RS", rating: 4, text: "Iluminação de qualidade para jogos noturnos.", date: "há 3 dias" },
            { name: "Thiago B.", initials: "TB", rating: 5, text: "Perfeito! Fácil de reservar pelo app.", date: "há 1 semana" },
            { name: "Fernanda L.", initials: "FL", rating: 4, text: "Ambiente seguro e organizado.", date: "há 10 dias" },
        ],
    },
    {
        id: 3,
        name: "Sunset Beach Club",
        address: "Av. Abolição, 3380 · Meireles",
        neighborhood: "Meireles, Fortaleza",
        sports: ["Beach Tennis", "Vôlei de Praia"],
        sportTags: ["Beach Tennis", "Vôlei"],
        rating: 4.9, reviewCount: 87,
        distance: "1.8 km", price: "R$ 80/h",
        premium: false,
        gradient: "linear-gradient(135deg, rgba(242,122,63,0.15), #E8D7BD)",
        desc: "Clube de beach sports à beira-mar com 4 quadras. Vista para o pôr do sol e drinks no bar.",
        amenities: ["Bar", "Vestiário", "Wi-Fi", "Ducha"],
        todaySlots: [
            { time: "07:00", status: "disponivel", spots: 4 },
            { time: "08:00", status: "ultimas", spots: 1 },
            { time: "17:00", status: "disponivel", spots: 4 },
            { time: "18:00", status: "reservado", spots: 0 },
        ],
        reviews: [
            { name: "Juliana F.", initials: "JF", rating: 5, text: "Vista linda para o mar! Pôr do sol jogando beach tênis. Perfeito!", date: "há 3 dias" },
            { name: "Carlos V.", initials: "CV", rating: 5, text: "Areia ótima, bar com drinks gelados. Vale cada centavo.", date: "há 1 semana" },
        ],
    },
    {
        id: 4,
        name: "Padel Master Club",
        address: "Rua Tibúrcio Cavalcante, 1190 · Dionísio Torres",
        neighborhood: "Dionísio Torres, Fortaleza",
        sports: ["Padel", "Tênis"],
        sportTags: ["Padel", "Tênis"],
        rating: 4.6, reviewCount: 63,
        distance: "3.1 km", price: "R$ 110/h",
        premium: false,
        gradient: "linear-gradient(135deg, rgba(173,153,0,0.15), #E8D7BD)",
        desc: "Clube exclusivo de padel com 5 quadras cobertas. Ambiente climatizado e equipamentos para locação.",
        amenities: ["Estacionamento", "Vestiário", "Loja", "Wi-Fi"],
        todaySlots: [
            { time: "08:00", status: "disponivel", spots: 4 },
            { time: "09:00", status: "disponivel", spots: 4 },
            { time: "16:00", status: "ultimas", spots: 2 },
            { time: "19:00", status: "disponivel", spots: 4 },
        ],
        reviews: [
            { name: "Beatriz N.", initials: "BN", rating: 5, text: "Melhor clube de padel do CE! Quadras excelentes.", date: "há 2 dias" },
            { name: "André P.", initials: "AP", rating: 4, text: "Ótimo ambiente, professores qualificados.", date: "há 5 dias" },
        ],
    },
    {
        id: 5,
        name: "SportZone Fortaleza",
        address: "Av. Godofredo Maciel, 2255 · Jóquei Clube",
        neighborhood: "Jóquei Clube, Fortaleza",
        sports: ["Basquete", "Futsal", "Handebol"],
        sportTags: ["Basquete", "Futsal"],
        rating: 4.5, reviewCount: 149,
        distance: "4.2 km", price: "R$ 95/h",
        premium: false,
        gradient: "linear-gradient(135deg, rgba(107,98,88,0.15), #E8D7BD)",
        desc: "Complexo esportivo com quadras poliesportivas cobertas. Ideal para basquete, futsal e handebol.",
        amenities: ["Estacionamento", "Vestiário", "Lanchonete", "Arquibancada"],
        todaySlots: [
            { time: "07:00", status: "disponivel", spots: 4 },
            { time: "09:00", status: "reservado", spots: 0 },
            { time: "18:00", status: "disponivel", spots: 4 },
            { time: "20:00", status: "ultimas", spots: 1 },
        ],
        reviews: [
            { name: "Roberto M.", initials: "RM", rating: 5, text: "Quadras excelentes para basquete. Piso de qualidade.", date: "há 4 dias" },
            { name: "Samira C.", initials: "SC", rating: 4, text: "Boa estrutura, preço acessível.", date: "há 1 semana" },
        ],
    },
    {
        id: 6,
        name: "Quadra Pro Tênis",
        address: "Rua Pereira Filgueiras, 540 · Aldeota",
        neighborhood: "Aldeota, Fortaleza",
        sports: ["Tênis"],
        sportTags: ["Tênis"],
        rating: 4.8, reviewCount: 92,
        distance: "2.7 km", price: "R$ 70/h",
        premium: false,
        gradient: "linear-gradient(135deg, rgba(47,175,160,0.1), #E8D7BD)",
        desc: "Quadras de tênis em saibro e cimento. Iluminação profissional para jogos noturnos e aulas com técnicos certificados.",
        amenities: ["Estacionamento", "Vestiário", "Locação de Raquetes", "Loja"],
        todaySlots: [
            { time: "07:00", status: "disponivel", spots: 2 },
            { time: "08:00", status: "ultimas", spots: 1 },
            { time: "17:00", status: "disponivel", spots: 2 },
            { time: "19:00", status: "disponivel", spots: 2 },
        ],
        reviews: [
            { name: "Felipe D.", initials: "FD", rating: 5, text: "Quadra de saibro impecável! Drenagem perfeita.", date: "há 2 dias" },
            { name: "Vanessa R.", initials: "VR", rating: 5, text: "Aulas excelentes, professores top.", date: "há 6 dias" },
        ],
    },
];

const DAYS: DayOption[] = [
    { label: "Hoje", date: "17" },
    { label: "Amanhã", date: "18" },
    { label: "Sáb", date: "19" },
    { label: "Dom", date: "20" },
    { label: "Seg", date: "21" },
    { label: "Ter", date: "22" },
    { label: "Qua", date: "23" },
];

const TIME_SLOTS: Record<"manha" | "tarde" | "noite", TimeSlot[]> = {
    manha: [
        { time: "07:00", price: "R$ 80", duration: "1h", spots: 4, status: "disponivel" },
        { time: "08:00", price: "R$ 80", duration: "1h", spots: 0, status: "reservado" },
        { time: "09:00", price: "R$ 90", duration: "1h", spots: 2, status: "ultimas" },
        { time: "10:00", price: "R$ 90", duration: "1h", spots: 4, status: "disponivel" },
        { time: "11:00", price: "R$ 100", duration: "1h", spots: 0, status: "indisponivel" },
    ],
    tarde: [
        { time: "13:00", price: "R$ 100", duration: "1h", spots: 4, status: "disponivel" },
        { time: "14:00", price: "R$ 100", duration: "1h", spots: 1, status: "ultimas" },
        { time: "15:00", price: "R$ 110", duration: "1h", spots: 4, status: "disponivel" },
        { time: "16:00", price: "R$ 110", duration: "1h", spots: 0, status: "reservado" },
        { time: "17:00", price: "R$ 120", duration: "1h", spots: 3, status: "disponivel" },
    ],
    noite: [
        { time: "18:00", price: "R$ 130", duration: "1h", spots: 4, status: "disponivel" },
        { time: "19:00", price: "R$ 140", duration: "1h", spots: 2, status: "ultimas" },
        { time: "20:00", price: "R$ 140", duration: "1h", spots: 4, status: "disponivel" },
        { time: "21:00", price: "R$ 130", duration: "1h", spots: 4, status: "disponivel" },
        { time: "22:00", price: "R$ 120", duration: "1h", spots: 0, status: "indisponivel" },
    ],
};

export async function getCourts(): Promise<Court[]> {
    // TODO integração: return (await fetch("/api/courts")).json();
    return FORTALEZA_COURTS;
}

export function getCourtById(id: number): Court {
    return FORTALEZA_COURTS.find((c) => c.id === id) ?? FORTALEZA_COURTS[0];
}

export function getCourtsSync(): Court[] {
    return FORTALEZA_COURTS;
}

export function getDays(): DayOption[] {
    return DAYS;
}

export function getTimeSlots() {
    return TIME_SLOTS;
}
