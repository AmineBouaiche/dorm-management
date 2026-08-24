export const APP_CONFIG = Object.freeze({
  name: "Residence",
  logo: null,
  apiBaseUrl: "/api",
  routes: Object.freeze({
    landing: "/",
    home: "/dashboard",
    login: "/login",
    register: "/register",
    rooms: "/rooms",
    bookings: "/bookings",
    account: "/account",
    bookingConfirm: "/booking/confirm",
    adminHome: "/admin",
  }),
});
