const rawLoginFlag = (import.meta.env.VITE_ENABLE_LOGIN ?? "true").toString().toLowerCase();

export const LOGIN_ENABLED = !["false", "0", "no", "off"].includes(rawLoginFlag);
