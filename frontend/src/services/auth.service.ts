// Service de autenticação.
// A estrutura de integração já está pronta — enquanto o backend não é usado,
// as funções resolvem com dados mockados (troque MOCK_AUTH para false para integrar).

const MOCK_AUTH = true;

export type UserType = "user" | "company";

export interface LoginData {
    email: string;
    password: string;
}

// Empresa entra com CNPJ + senha (não usa e-mail)
export interface CompanyLoginData {
    cnpj: string;
    password: string;
}

export interface SignupData {
    name: string;
    email: string;
    password: string;
}

export interface CompanySignupData {
    cnpj: string;
    name: string;
    email: string;
    password: string;
    street: string;
    number: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
}

export async function login(data: LoginData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        return { token: "mock-token", user: { name: "João Silva", email: data.email } };
    }

    const res = await fetch("/api/auth/user-login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        throw new Error("Erro ao fazer o login");
    }

    return res.json();
}

export async function loginCompany(data: CompanyLoginData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        return { token: "mock-token", company: { name: "Arena Beira-Mar", cnpj: data.cnpj } };
    }

    const res = await fetch("/api/auth/company-login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        throw new Error("Erro ao fazer o login");
    }

    return res.json();
}

export async function signup(data: SignupData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1400));
        return { token: "mock-token", user: { name: data.name, email: data.email } };
    }

    const res = await fetch("/api/auth/user-signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        throw new Error("Erro ao criar a conta");
    }

    return res.json();
}

export async function signupCompany(data: CompanySignupData) {
    if (MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 1400));
        return { token: "mock-token", company: { name: data.name, email: data.email } };
    }

    const res = await fetch("/api/auth/company-signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        throw new Error("Erro ao criar a conta");
    }

    return res.json();
}
