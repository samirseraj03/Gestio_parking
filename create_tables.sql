
CREATE DATABASE gestion_parking_db;

// crear base de dades

CREATE TABLE plazas(
    id INTEGER PRIMARY KEY,
    numero INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 48),
    estado VARCHAR NOT NULL CHECK ( estado = 'SI' OR estado = 'NO')
    );

CREATE TABLE estacionamientos(
    
    id SERIAL PRIMARY KEY,
    fecha_hora_entrada TIMESTAMP WITHOUT TIME ZONE DEFAULT default to_char(now()::TIMESTAMP , 'yyyy-mm-dd hh24:mi:ss')::timestamp ,
    fecha_hora_salida TIMESTAMP WITHOUT TIME ZONE default to_char(now()::TIMESTAMP , 'yyyy-mm-dd hh24:mi:ss')::timestamp ,
    matricula VARCHAR NOT NULL,
    plaza_id INTEGER NOT NULL,
    importe NUMERIC NOT NULL,
    FOREIGN KEY (plaza_id) REFERENCES plazas(id)
    _import_total NUMERIC DEFAULT (0.00)


    );


CREATE TABLE preus (

	id SERIAL PRIMARY KEY ,
	mes INTEGER not null ,
	preus_minut NUMERIC 

);


// COMMENT desplegar las plazas

DO $$
DECLARE
  id_counter INTEGER := 0;
  n_counter integer := 1;
BEGIN
  WHILE n_counter <= 48
  LOOP
    INSERT INTO plazas(id , numero , estado)
	VALUES (id_counter , n_counter , 'NO');
	id_counter := id_counter + 1;
	n_counter := n_counter + 1;
  END LOOP;
END $$;

// desplegar els preus
DO $$
DECLARE
  id_counter INTEGER := 0;
  preus numeric := 0.01;
  _mes integer := 1;
BEGIN
  WHILE _mes <= 12
  LOOP
    INSERT INTO preus(id , mes , preus_minut)
	VALUES (id_counter , _mes , preus);
	id_counter := id_counter + 1;
	preus := preus + 0.02;
	_mes := _mes + 1;
  END LOOP;
END $$;


