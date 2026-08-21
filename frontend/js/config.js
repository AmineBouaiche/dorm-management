export const APP_CONFIG = Object.freeze({
  name: "Residence",
  logo: null,
  apiBaseUrl: "/api",
  routes: Object.freeze({
    home: "/",
    login: "/login",
    register: "/register",
    session: "/session",
    rooms: "/rooms",
    bookingConfirm: "/booking/confirm",
    adminSession: "/admin/session",
  }),
});
