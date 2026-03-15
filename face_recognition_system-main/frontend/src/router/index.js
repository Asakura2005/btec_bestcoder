// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Home from '../views/HomeView.vue';
import Login from '../views/Login.vue';
import Employees from '../views/Employees.vue';
import Attendance from '../views/Attendance.vue';
import Reports from '../views/Reports.vue';
import ChangePasswordPage from '@/views/ChangePasswordPage.vue';
import ResetPassword from '@/views/ResetPassword.vue';

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: Home, 
    meta: { requiresAuth: true, role: 'admin' }
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: Login 
  },
  { 
    path: '/employees', 
    name: 'Employees', 
    component: Employees, 
    meta: { requiresAuth: true, role: 'employee' }
  },
  { 
    path: '/attendance', 
    name: 'Attendance', 
    component: Attendance, 
    meta: { requiresAuth: false }
  },
  { 
    path: '/reports', 
    name: 'Reports', 
    component: Reports, 
    meta: { requiresAuth: true, role: 'admin' }
  },
  { 
    path: '/employee/change-password', 
    name: 'ChangePasswordPage', 
    component: ChangePasswordPage, 
    meta: { requiresAuth: true, role: 'employee' }
  },
  {
      path: '/reset-password',
      name: 'ResetPassword',
      component: ResetPassword
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  
  // Đợi store khởi tạo xong
  if (!authStore.isInitialized) {
    await authStore.initializeFromStorage();
  }
  
  console.log('🔍 Router guard:', {
    to: to.name,
    from: from.name,
    requiresAuth: to.meta.requiresAuth,
    isAuthenticated: authStore.isAuthenticated,
    userRole: authStore.user?.role,
    mustChangePassword: authStore.user?.must_change_password,
    hasToken: !!authStore.token,
  });

  const isAuthenticated = authStore.isAuthenticated;
  const userRole = authStore.user?.role;
  const mustChangePassword = authStore.user?.must_change_password;
  const targetRequiresAuth = to.meta.requiresAuth;
  const targetRequiredRole = to.meta.role;

  // 1. Nếu đang đi đến trang Login
  if (to.name === 'Login') {
    // Nếu chưa đăng nhập hoặc đã logout, cho phép vào login
    if (!isAuthenticated) {
      console.log('User not authenticated, allowing access to login page.');
      next();
      return;
    }
    
    // Nếu đã đăng nhập, redirect đến trang phù hợp
    console.log('User already authenticated, redirecting from login page.');
    if (userRole === 'admin') {
      next({ name: 'Home' });
    } else if (userRole === 'employee') {
      if (mustChangePassword) {
        next({ name: 'ChangePasswordPage' });
      } else {
        next({ name: 'Employees' });
      }
    } else {
      // Nếu role không xác định, cho phép vào login
      console.log('Unknown role, allowing login access.');
      next();
    }
    return;
  }

  // 2. Nếu route yêu cầu xác thực
  if (targetRequiresAuth) {
    if (!isAuthenticated) {
      console.log('Route requires auth but user not authenticated. Redirecting to login.');
      next({ name: 'Login', query: { redirect: to.fullPath } });
      return;
    }

    // Nếu đã xác thực, kiểm tra cờ must_change_password (chỉ áp dụng cho employee)
    if (userRole === 'employee' && mustChangePassword) {
      // Nếu employee phải đổi mật khẩu và không phải là trang đổi mật khẩu, chuyển hướng
      if (to.name !== 'ChangePasswordPage') {
        console.log('Employee must change password. Redirecting to change password page.');
        next({ name: 'ChangePasswordPage' });
        return;
      }
    }

    // Kiểm tra quyền hạn (role)
    if (targetRequiredRole && userRole !== targetRequiredRole) {
      console.log(`User role (${userRole}) does not match required role (${targetRequiredRole}). Redirecting.`);
      if (userRole === 'admin') {
        next({ name: 'Home' });
      } else if (userRole === 'employee') {
        // Kiểm tra xem employee có cần đổi mật khẩu không
        if (mustChangePassword) {
          next({ name: 'ChangePasswordPage' });
        } else {
          next({ name: 'Employees' });
        }
      } else {
        // Nếu vai trò không xác định, đăng xuất và về login
        console.log('Unknown role, logging out and redirecting to login.');
        authStore.logout();
        next({ name: 'Login' });
      }
      return;
    }
    
    // Nếu mọi thứ ổn, cho phép truy cập
    console.log('User authenticated and authorized. Proceeding to route.');
    next();

  } else {
    // 3. Các route không yêu cầu xác thực
    console.log('Public route. Proceeding.');
    next();
  }
});

export default router;