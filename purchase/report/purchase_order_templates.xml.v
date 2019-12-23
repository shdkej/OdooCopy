
            <div class="row">
                <div class="col-xs-4 pull-right">
                    <table class="table table-condensed">
                        <tr t-foreach="o.product" t-as="line" class="border-black">
                            <td><strong>Total Without Taxes</strong></td>
                            <td class="text-right">
                                <span t-field="line.total_price"/>
                            </td>
                        </tr>
                        <tr>
                            <td>Taxes</td>
                            <td class="text-right">
                                <span t-field="line.original_count"/>
                            </td>
                        </tr>
                        <tr class="border-black">
                            <td><strong>Total</strong></td>
                            <td class="text-right">
                                <span t-field="o.total_price"/>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
