-- DROP DATABASE base_documental;
CREATE DATABASE IF NOT EXISTS base_documental;
USE base_documental;

-- Tabla Nivel de Protección
CREATE TABLE nivel_proteccion (
    id_nivel INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(100) NOT NULL
);

-- Tabla Metodo Recepcion
CREATE TABLE metodo_recepcion (
    id_metodo INT PRIMARY KEY AUTO_INCREMENT,
    metodo VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla Procedencia
CREATE TABLE procedencia (
    id_proc INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(150) NOT NULL UNIQUE
);

-- Tabla Precedencia
CREATE TABLE precedencia (
    id_precedencia INT PRIMARY KEY AUTO_INCREMENT,
    tipo VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla Receptor (modificado: ahora incluye nombre)
CREATE TABLE receptor (
    id_receptor INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(45)
);

-- Tabla Palabras Clave
CREATE TABLE palabras_clave (
    id_keyword INT PRIMARY KEY AUTO_INCREMENT,
    palabra VARCHAR(50) NOT NULL
);

-- Tabla Area y Subárea
CREATE TABLE area (
    id_area INT PRIMARY KEY AUTO_INCREMENT,
    nombre_area VARCHAR(100) NOT NULL
);

CREATE TABLE subarea (
    id_subarea INT PRIMARY KEY AUTO_INCREMENT,
    id_area INT NOT NULL,
    nombre_subarea VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_area) REFERENCES area(id_area)
);

-- Tabla Acuerdo
CREATE TABLE Acuerdo (
    id_Acuerdo INT PRIMARY KEY AUTO_INCREMENT,
    nombre_Acuerdo VARCHAR(100) NOT NULL
);

CREATE TABLE area_has_Acuerdo (
    area_id_area INT NOT NULL,
    Acuerdo_id_Acuerdo INT NOT NULL,
    PRIMARY KEY (area_id_area, Acuerdo_id_Acuerdo),
    FOREIGN KEY (area_id_area) REFERENCES area(id_area),
    FOREIGN KEY (Acuerdo_id_Acuerdo) REFERENCES Acuerdo(id_Acuerdo)
);

-- Tabla Documento (modificado: id_nivel, id_metodo, id_proc, id_precedencia como claves foráneas)
CREATE TABLE documento (
    id_documento INT PRIMARY KEY AUTO_INCREMENT,
    numero VARCHAR(20),
    asunto VARCHAR(255),
    id_precedencia INT,
    id_proc INT,
    fecha DATE,
    idea_principal TEXT,
    clasificacion VARCHAR(50),
    ruta_archivo VARCHAR(255),
    id_metodo INT,
    id_nivel INT,
    receptor_id_receptor INT,
    FOREIGN KEY (id_precedencia) REFERENCES precedencia(id_precedencia),
    FOREIGN KEY (id_proc) REFERENCES procedencia(id_proc),
    FOREIGN KEY (id_metodo) REFERENCES metodo_recepcion(id_metodo),
    FOREIGN KEY (id_nivel) REFERENCES nivel_proteccion(id_nivel),
    FOREIGN KEY (receptor_id_receptor) REFERENCES receptor(id_receptor)
);

-- Tabla relación documento-área
CREATE TABLE documento_has_area (
    documento_id_documento INT NOT NULL,
    area_id_area INT NOT NULL,
    PRIMARY KEY (documento_id_documento, area_id_area),
    FOREIGN KEY (documento_id_documento) REFERENCES documento(id_documento),
    FOREIGN KEY (area_id_area) REFERENCES area(id_area)
);

-- Tabla relación documento-palabra_clave
CREATE TABLE documento_palabra_clave (
    id_documento INT NOT NULL,
    id_keyword INT NOT NULL,
    PRIMARY KEY (id_documento, id_keyword),
    FOREIGN KEY (id_documento) REFERENCES documento(id_documento),
    FOREIGN KEY (id_keyword) REFERENCES palabras_clave(id_keyword)
);


INSERT INTO nivel_proteccion (codigo, descripcion) VALUES
('NP-AS','Alto Secreto'),
('NP-Secreto','Secreto'),
('NP-Conf','Confidencial'),
('NP-Rest','Restringido'),
('NP-PUO','Para Uso Oficial'),
('Sin Clasificacion','Sin Clasificación')
;

INSERT INTO metodo_recepcion (metodo) VALUES
('Correo electrónico institucional @naval.sm'),
('Cartero'),
('Correo naval oficial @semar.gob.mx');


-- Ejemplos de procedencias
INSERT INTO procedencia (nombre) VALUES
('UNIDETEC'),
('DIGABAS'),
('DIGADMON'),
('Región Naval 1'),
('Zona Naval 1'),
('ARM "Juarez"'),
('ARM "Circini" PI-1416');


INSERT INTO precedencia (tipo) VALUES
('Instantáneo'),
('Extraurgente'),
('Urgente'),
('Ordinario'),
('N/A');