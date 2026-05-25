self.addEventListener('push', event => {
  const data    = event.data ? event.data.json() : {};
  const title   = data.title || 'Tennis Club';
  const options = {
    body:    data.body || 'Nuova notifica',
    icon:    '/static/img/icon.png',
    badge:   '/static/img/icon.png',
    vibrate: [200, 100, 200],
    tag:     'tennis-booking',
    data:    { url: '/admin' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/admin';
  event.waitUntil(clients.openWindow(url));
});
