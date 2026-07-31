const http = require('http');

const data = JSON.stringify({
  email: 'admin@company.com',
  password: 'admin'
});

const req = http.request({
  hostname: '127.0.0.1',
  port: 8088,
  path: '/api/v1/auth/login',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
}, (res) => {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    console.log('STATUS:', res.statusCode);
    console.log('RESPONSE:', JSON.stringify(JSON.parse(body), null, 2));
  });
});

req.on('error', (e) => {
  console.error('ERROR:', e.message);
});

req.write(data);
req.end();
