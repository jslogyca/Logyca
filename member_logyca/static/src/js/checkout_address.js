/**
 * Extension Odoo 17 – Exponer rango_type, how_findout y x_sector_id en el checkout
 */
import { registry } from '@web/core/registry';
import CheckoutAddress from 'website_sale/static/src/components/CheckoutAddress/checkout_address';
import { useService } from '@web/core/utils/hooks';

export default class CheckoutAddressCustom extends CheckoutAddress {
    setup() {
        super.setup();
        const modelFields = this.env.models['res.partner'].fields;

        // Exponer las opciones definidas en el modelo para rango_type y how_findout
        this.selectionOptions = {
            rango_type: modelFields.rango_type.selection.map(([value, label]) => ({ value, label })),
            how_findout: modelFields.how_findout.selection.map(([value, label]) => ({ value, label })),
        };

        // Inyectar RPC para cargar sectores
        this.rpc = useService('rpc');
        this.sectors = [];
        this.loadSectors();
    }

    async loadSectors() {
        const sectors = await this.rpc({
            model: 'logyca.sectors',
            method: 'search_read',
            args: [[], ['id', 'name']],
        });
        this.sectors = sectors;
        // Inicializar x_sector_id si no existe
        if (!this.state.x_sector_id) {
            this.updateState({ x_sector_id: '' });
        }
    }

    get state() {
        return {
            ...super.state,
            rango_type:    super.state.rango_type    || '',
            how_findout:   super.state.how_findout   || '',
            x_sector_id:   super.state.x_sector_id   || '',
        };
    }

    getSectorOptions() {
        return this.sectors.map(s => ({ value: s.id, label: s.name }));
    }
}

// Registrar la extensión
registry.category('checkout.custom').add(
    'checkout_address_custom',
    CheckoutAddressCustom,
    { position: 30, target: 'checkout-address' }
);
