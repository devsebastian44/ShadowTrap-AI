// ShadowTrap AI - MongoDB Initialization
db = db.getSiblingDB('shadowtrap');

db.createUser({
  user: 'shadowtrap_user',
  pwd: 'shadowtrap_pass',
  roles: [
    { role: 'readWrite', db: 'shadowtrap' }
  ]
});

db.createCollection('login_attempts');
db.createCollection('commands');
db.createCollection('sessions');
db.createCollection('alerts');

print('✅ ShadowTrap AI database initialized');
