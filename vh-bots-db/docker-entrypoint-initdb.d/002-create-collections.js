db._useDatabase('villagerhaven');
try {
  db._create('requests');
}
catch {}

try {
  db._create('archived-requests');
}
catch {}

try {
  db._create('queues');
}
catch {}

try {
  db._create('member-game-info');
}
catch {}

try {
  db._create('drawings');
}
catch {}

try {
  db._create('members');
}
catch {}

try {
  db._create('member-preferences');
}
catch {}

try {
  db._create('redemptions', { keyOptions: { type: 'autoincrement' }});
}
catch {}

try {
  db._create('settings');
}
catch {}

try {
  db._create('awards');
}
catch {}
