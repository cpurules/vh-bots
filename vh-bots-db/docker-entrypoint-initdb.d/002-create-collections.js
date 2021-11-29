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
  db._create('drawings');
}
catch {}
