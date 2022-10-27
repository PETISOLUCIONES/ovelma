odoo.define('pos_info_customer_peti.ClientDetailsEdit', function(require){
    "use strict";

    var models = require('point_of_sale.models');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

const ClientDetailsEditFields = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
        constructor() {
                super(...arguments);
            }

        captureChange(event) {
            self = this
            super.captureChange(event)
            $(document).on("change", "select[name='company_type']", function()
                {
                    self.onchange_company_type();
                });
                $(document).on("change", "select[name='l10n_latam_identification_type_id']", function()
                {
                    self.onchange_document_type();
                });

                $(document).on("change", "input[name='vat_num']", function()
                {
                    self.update_nit_cod_verification();
                });
                $(document).on("blur", "input[name='firstname']", function()
                {
                    self.update_name();
                });
                $(document).on("blur", "input[name='other_name']", function()
                {
                    self.update_name();
                });
                $(document).on("blur", "input[name='lastname']", function()
                {
                    self.update_name();
                });
                $(document).on("blur", "input[name='other_lastname']", function()
                {
                    self.update_name();
                });
        }

        saveChanges() {
            let processedChanges = {};
            if(!this.props.partner.name){
                    if(this.changes.firstname && this.changes.firstname != ''){
                        this.changes['name'] = $("input[name='name']").val()
                    }
                }
            for (let [key, value] of Object.entries(this.changes)) {
                if (this.intFields.includes(key)) {
                    processedChanges[key] = parseInt(value) || false;
                } else {
                    processedChanges[key] = value;
                }
            }
            if ((!this.props.partner.name && !processedChanges.name) ||
                processedChanges.name === '' ){
                return this.showPopup('ErrorPopup', {
                  title: _t('A Customer Name Is Required'),
                });
            }
            processedChanges.id = this.props.partner.id || false;
            this.trigger('save-changes', { processedChanges });
        }

        update_name()
        {
            var firstname =  $("input[name='firstname']").val();
            var other_name =  $("input[name='other_name']").val();
            var lastname =  $("input[name='lastname']").val();
            var other_lastname =  $("input[name='other_lastname']").val();
            var name = firstname + ' ' + other_name + ' ' + lastname + ' ' + other_lastname
            $("input[name='name']").val(name.toUpperCase());
            this.changes['name'] = name.toUpperCase();
        }

        onchange_document_type()
        {
            var document_type =  $("select[name='l10n_latam_identification_type_id']").val();

            if (document_type == '4'){
                $("select[name='vat_type']").val("31");
                $("select[name='company_type']").val("company");}
            else if (document_type == '5'){
                $("select[name='vat_type']").val("13");
                $("select[name='company_type']").val("person");}
            else if (document_type == '7'){
                $("select[name='vat_type']").val("12");
                $("select[name='company_type']").val("person");}
            else if (document_type == '2') {
                $("select[name='vat_type']").val("41");
                $("select[name='company_type']").val("person");}
            else if (document_type == '3'){
                $("select[name='vat_type']").val("22");
                $("select[name='company_type']").val("person");}
            else if (document_type == '10'){
                $("select[name='vat_type']").val("");
                $("select[name='company_type']").val("person");}
            else if (document_type == '13'){
                $("select[name='vat_type']").val("");
                $("select[name='company_type']").val("person");}
            else if (document_type == '10'){
                $("select[name='vat_type']").val("");
                $("select[name='company_type']").val("person");}
            else if (document_type == '6'){
                $("select[name='vat_type']").val("11");
                $("select[name='company_type']").val("person");}

            var company_type_val =  $("select[name='company_type']").val()
            if (company_type_val == "person"){
                $("input[name='firstname']").show();
                $("input[name='other_name']").show();
                $("input[name='lastname']").show();
                $("input[name='other_lastname']").show();
                $(".client-names").show();
                $("input[name='name']").hide();
                $("#cumpleaños").show();
                //$("input[name='name']").val("");
                $("#vat_vd").hide();
                //$("select[name='l10n_latam_identification_type_id']").val("id_document");
                //$("select[name='company_type']").val("person");
            }else{
                $("input[name='firstname']").hide();
                $("input[name='other_name']").hide();
                $("input[name='lastname']").hide();
                $("input[name='other_lastname']").hide();
                $(".client-names").hide();
                $("input[name='name']").show();
                $("#cumpleaños").hide();
                //$("input[name='name']").val("");
                $("#vat_vd").show();
                //$("select[name='l10n_latam_identification_type_id']").val("rut");
                //$("select[name='company_type']").val("company");
            }
        }

        onchange_company_type(){
            var company_type_val =  $("select[name='company_type']").val();

             var docu = $("input[name='vat_num']").val();
             $("input[name='vat']").val(docu);
            if (company_type_val == "person"){
                $("input[name='firstname']").show();
                $("input[name='other_name']").show();
                $("input[name='lastname']").show();
                $("input[name='other_lastname']").show();
                $(".client-names").show();
                $("input[name='name']").hide();
                $("#cumpleaños").show();
                //$("input[name='name']").val("");
                $("#vat_vd").hide();
                $("select[name='l10n_latam_identification_type_id']").val("id_document");
                $("select[name='vat_type']").val("13");
                //$("select[name='company_type']").val("person");
            }else{
                $("input[name='firstname']").hide();
                $("input[name='other_name']").hide();
                $("input[name='lastname']").hide();
                $("input[name='other_lastname']").hide();
                $(".client-names").hide();
                $("input[name='name']").show();
                $("#cumpleaños").hide();
                //$("input[name='name']").val("");
                $("#vat_vd").show();
                $("select[name='l10n_latam_identification_type_id']").val("rut");
                $("select[name='vat_type']").val("31");
                //$("select[name='company_type']").val("company");
            }
        }

        update_nit_cod_verification()
        {
            var doc_type = $("select[name='l10n_latam_identification_type_id']").val()
            var myNit =  $("input[name='vat_num']").val()
            if(doc_type=="rut")
            {

                var vpri,
                x,
                y,
                z;

                // Se limpia el Nit
                myNit = myNit.replace(/\s/g, ""); // Espacios
                myNit = myNit.replace(/,/g, ""); // Comas
                myNit = myNit.replace(/\./g, ""); // Puntos
                myNit = myNit.replace(/-/g, ""); // Guiones

                // Se valida el nit
                if (isNaN(myNit)) {
                    console.log("El nit/cédula '" + myNit + "' no es válido(a).");
                    return "";
                };

                // Procedimiento
                vpri = new Array(16);
                z = myNit.length;

                vpri[1] = 3;
                vpri[2] = 7;
                vpri[3] = 13;
                vpri[4] = 17;
                vpri[5] = 19;
                vpri[6] = 23;
                vpri[7] = 29;
                vpri[8] = 37;
                vpri[9] = 41;
                vpri[10] = 43;
                vpri[11] = 47;
                vpri[12] = 53;
                vpri[13] = 59;
                vpri[14] = 67;
                vpri[15] = 71;

                x = 0;
                y = 0;
                for (var i = 0; i < z; i++) {
                    y = (myNit.substr(i, 1));
                    // console.log ( y + "x" + vpri[z-i] + ":" ) ;

                    x += (y * vpri[z - i]);
                    // console.log ( x ) ;
                }

                y = x % 11;
                // console.log ( y ) ;

                var doc_num_code = (y > 1) ? 11 - y : y;

                $("input[name='vat_vd']").val(doc_num_code);
                $("input[name='vat']").val(myNit +'-'+ doc_num_code );
            }else{
                $("input[name='vat']").val(myNit);
            }

        }
    };
    Registries.Component.extend(ClientDetailsEdit, ClientDetailsEditFields);

    return ClientDetailsEdit;
});