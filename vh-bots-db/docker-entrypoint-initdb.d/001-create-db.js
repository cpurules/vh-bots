try {
  db._createDatabase('villagerhaven');
}
catch (e) {
  if (e.message.indexOf('duplicate database name')) {
    console.log('villagerhaven database already exists');
  }
}
