import { useMutation } from "@tanstack/react-query";
import { signup, signupCompany } from "../../../services/auth.service";


export function useSignup() {
    return useMutation({
        mutationFn: signup
    })
}

export function useSignupCompany() {
    return useMutation({
        mutationFn: signupCompany
    })
}
