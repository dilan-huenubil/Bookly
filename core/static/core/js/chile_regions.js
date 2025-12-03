document.addEventListener('DOMContentLoaded', function () {
    if (window.initChileRegions) {
        window.initChileRegions('regionSelect', 'comunaSelect');
    }
});

(function () {
    // Dataset completo de regiones y comunas de Chile (abreviado para casos comunes; puedes ampliar si falta alguna).
    const DATA = {
        "REGIÓN DE ARICA Y PARINACOTA": ["Arica","Camarones","Putre","General Lagos"],
        "REGIÓN DE TARAPACÁ": ["Iquique","Alto Hospicio","Pica","Pozo Almonte","Huara","Camiña","Colchane"],
        "REGIÓN DE ANTOFAGASTA": ["Antofagasta","Mejillones","Sierra Gorda","Taltal","Calama","San Pedro de Atacama","Ollagüe","María Elena","Tocopilla"],
        "REGIÓN DE ATACAMA": ["Copiapó","Caldera","Tierra Amarilla","Chañaral","Diego de Almagro","Vallenar","Freirina","Huasco","Alto del Carmen"],
        "REGIÓN DE COQUIMBO": ["La Serena","Coquimbo","Andacollo","La Higuera","Paihuano","Vicuña","Illapel","Canela","Los Vilos","Salamanca","Ovalle","Combarbalá","Monte Patria","Punitaqui","Río Hurtado"],
        "REGIÓN DE VALPARAÍSO": ["Valparaíso","Viña del Mar","Concón","Quilpué","Villa Alemana","Casablanca","Juan Fernández","Puchuncaví","Quintero","Algarrobo","Cartagena","El Quisco","El Tabo","San Antonio","Santo Domingo","Isla de Pascua","Los Andes","San Esteban","Calle Larga","Rinconada","La Ligua","Papudo","Cabildo","Zapallar","Petorca","San Felipe","Catemu","Llaillay","Panquehue","Putaendo","Santa María"],
        "REGIÓN METROPOLITANA": ["Santiago","Cerrillos","Cerro Navia","Conchalí","El Bosque","Estación Central","Huechuraba","Independencia","La Cisterna","La Florida","La Granja","La Pintana","La Reina","Las Condes","Lo Barnechea","Lo Espejo","Lo Prado","Macul","Maipú","Ñuñoa","Pedro Aguirre Cerda","Peñalolén","Providencia","Pudahuel","Quilicura","Quinta Normal","Recoleta","Renca","San Joaquín","San Miguel","San Ramón","Vitacura","Puente Alto","Pirque","San José de Maipo","Colina","Lampa","Tiltil","San Bernardo","Buin","Calera de Tango","Paine","Melipilla","María Pinto","Curacaví","San Pedro","Talagante","El Monte","Isla de Maipo","Padre Hurtado","Peñaflor"],
        "REGIÓN DEL LIBERTADOR GENERAL BERNARDO O'HIGGINS": ["Rancagua","Codegua","Coinco","Coltauco","Doñihue","Graneros","Las Cabras","Machalí","Malloa","Mostazal","Olivar","Peumo","Pichidegua","Quinta de Tilcoco","Rengo","Requínoa","San Vicente","Pichilemu","La Estrella","Litueche","Marchihue","Navidad","Paredones","San Fernando","Chépica","Chimbarongo","Lolol","Nancagua","Palmilla","Peralillo","Placilla","Pumanque","Santa Cruz"],
        "REGIÓN DEL MAULE": ["Talca","Constitución","Curepto","Empedrado","Maule","Pelarco","Pencahue","Río Claro","San Clemente","San Rafael","Cauquenes","Chanco","Pelluhue","Curicó","Hualañé","Licantén","Molina","Rauco","Romeral","Sagrada Familia","Teno","Vichuquén","Linares","Colbún","Longaví","Parral","Retiro","San Javier","Villa Alegre","Yerbas Buenas"],
        "REGIÓN DE ÑUBLE": ["Chillán","Chillán Viejo","Quillón","Bulnes","San Ignacio","El Carmen","Pinto","Coihueco","San Nicolás","Ñiquén","San Carlos","Treguaco","San Fabián","Ninhue","Ránquil","Portezuelo","Cobquecura"],
        "REGIÓN DEL BIOBÍO": ["Concepción","Coronel","Chiguayante","Florida","Hualqui","Lota","Penco","San Pedro de la Paz","Santa Juana","Talcahuano","Tomé","Hualpén","Los Ángeles","Antuco","Cabrero","Laja","Mulchén","Nacimiento","Negrete","Quilaco","Quilleco","San Rosendo","Santa Bárbara","Tucapel","Yumbel","Alto Biobío","Arauco","Cañete","Contulmo","Curanilahue","Lebu","Los Álamos","Tirúa"],
        "REGIÓN DE LA ARAUCANÍA": ["Temuco","Carahue","Cholchol","Cunco","Curarrehue","Freire","Galvarino","Gorbea","Lautaro","Loncoche","Melipeuco","Nueva Imperial","Padre Las Casas","Perquenco","Pitrufquén","Pucon","Saavedra","Teodoro Schmidt","Toltén","Vilcún","Villarrica","Angol","Collipulli","Curacautín","Ercilla","Lonquimay","Los Sauces","Lumaco","Purén","Renaico","Traiguén","Victoria"],
        "REGIÓN DE LOS RÍOS": ["Valdivia","Corral","Lanco","Los Lagos","Máfil","Mariquina","Paillaco","Panguipulli","La Unión","Futrono","Lago Ranco","Río Bueno"],
        "REGIÓN DE LOS LAGOS": ["Puerto Montt","Calbuco","Cochamó","Fresia","Frutillar","Los Muermos","Llanquihue","Maullín","Puerto Varas","Castro","Ancud","Chonchi","Curaco de Vélez","Dalcahue","Puqueldón","Queilén","Quellón","Quemchi","Quinchao","Osorno","Puerto Octay","Purranque","Puyehue","Río Negro","San Juan de la Costa","San Pablo","Chaitén","Futaleufú","Hualaihué","Palena"],
        "REGIÓN DE AYSÉN": ["Coyhaique","Lago Verde","Aysén","Cisnes","Guaitecas","Cochrane","O'Higgins","Tortel","Chile Chico","Río Ibáñez"],
        "REGIÓN DE MAGALLANES Y DE LA ANTÁRTICA CHILENA": ["Punta Arenas","Laguna Blanca","Río Verde","San Gregorio","Porvenir","Primavera","Timaukel","Natales","Torres del Paine","Cabo de Hornos","Antártica"],
    };

    function populateSelect(select, options) {
        select.innerHTML = '';
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = select.id === 'regionSelect' ? 'Seleccionar región' : 'Seleccionar comuna';
        select.appendChild(placeholder);
        options.forEach(opt => {
            const o = document.createElement('option');
            o.value = opt;
            o.textContent = opt;
            select.appendChild(o);
        });
    }

    function initChileRegions(regionId, comunaId) {
        const regionSelect = document.getElementById(regionId);
        const comunaSelect = document.getElementById(comunaId);
        if (!regionSelect || !comunaSelect) return;

        const regions = Object.keys(DATA);
        populateSelect(regionSelect, regions);

        regionSelect.addEventListener('change', function () {
            const region = regionSelect.value;
            const comunas = DATA[region] || [];
            populateSelect(comunaSelect, comunas);
            // Scroll to top after repopulate
            comunaSelect.scrollTop = 0;
        });

        // Preselección si vienen valores desde el servidor
        const initialRegion = regionSelect.dataset.initialRegion;
        const initialComuna = comunaSelect.dataset.initialComuna;
        if (initialRegion && DATA[initialRegion]) {
            regionSelect.value = initialRegion;
            const comunas = DATA[initialRegion] || [];
            populateSelect(comunaSelect, comunas);
            if (initialComuna && comunas.includes(initialComuna)) {
                comunaSelect.value = initialComuna;
            }
        } else {
            if (regionSelect.value && DATA[regionSelect.value]) {
                populateSelect(comunaSelect, DATA[regionSelect.value]);
            } else {
                populateSelect(comunaSelect, []);
            }
        }

        // Mejorar accesibilidad: permitir buscar escribiendo rápidamente
        comunaSelect.addEventListener('keyup', function(e){
            // Navegación nativa del select ya cubre esto; placeholder para extender.
        });
    }

    window.initChileRegions = initChileRegions;
})();
