from custom.ewsghana.tests.handlers.utils import EWSScriptTest, restore_location_products, \
    assign_products_to_location


class StockOnHandTest(EWSScriptTest):

    def test_stock_on_hand(self):
        a = """
           5551234 > soh lf 50.0
           5551234 < Dear stella, thank you for reporting the commodities you have in stock.
           5551234 > soh lf 50.0 mc 25.0
           5551234 < Dear stella, thank you for reporting the commodities you have in stock.
           5551234 > SOH LF 50.0 MC 25.0
           5551234 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.run_script(a)

    def test_stockout(self):
        a = """
           5551234 > soh lf 0.0 mc 0.0
           5551234 < Dear stella, these items are stocked out: lf mc. Please order lf 45 mc 22.
           """
        self.run_script(a)

    def test_stockout_no_consumption(self):
        a = """
           5551234 > soh ng 0.0
           5551234 < Dear stella, these items are stocked out: ng.
           """
        self.run_script(a)

    def test_low_supply(self):
        a = """
           5551234 > soh lf 7.0 mc 9.0
           5551234 < Dear stella, these items need to be reordered: lf mc. Please order lf 58 mc 22.
           """
        self.run_script(a)

    def test_low_supply_no_consumption(self):
        a = """
           5551234 > soh ng 3.0
           5551234 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.run_script(a)

    def test_over_supply(self):
        a = """
            5551234 > soh lf 100.0 mc 100.0
            5551234 < Dear stella, these items are overstocked: lf mc. The district admin has been informed.
        """
        self.run_script(a)

    def test_soh_and_receipt(self):
        a = """
           5551234 > soh lf 90.90 mc 25.0
           5551234 < Dear stella, thank you for reporting the commodities you have. You received lf 90.
           """
        self.run_script(a)

    def test_combined1(self):
        second_message = "Dear super, Test RMS is experiencing the following problems: stockouts Lofem; " \
                         "below reorder level Male Condom"
        last_message = "Dear stella, these items are stocked out: lf. these items need to be reordered: mc. " \
                       "Please order lf 45 mc 40."
        a = """
           5551234 > soh lf 0.0 mc 1.0
           222222  < %s
           5551234 < %s
           """ % (second_message, last_message)
        self.run_script(a)

    def test_combined2(self):
        second_message = "Dear super, Test RMS is experiencing the following problems: stockouts Male Condom; " \
                         "below reorder level Micro-G"
        third_and_last_message = "Dear stella, these items are stocked out: mc. " \
                                 "these items need to be reordered: mg. Please order mc 22 mg 40."
        fifth_message = "Dear super, Test RMS is experiencing the following problems: stockouts Male Condom; " \
                        "below reorder level Micro-G; overstocked Lofem"
        last_message = "Dear stella, these items are stocked out: mc. these items need to be reordered: mg. " \
                       "Please order mc 22 mg 40."
        a = """
           5551234 > soh mc 0.0 mg 1.0
           222222 < %s
           5551234 < %s
           5551234 > soh mc 0.0 mg 1.0 lf 100.0
           222222 < %s
           5551234 < %s
           """ % (second_message, third_and_last_message, fifth_message, last_message)
        self.run_script(a)

    def test_combined3(self):
        second_message = "Dear super, Test RMS is experiencing the following problems: stockouts Male Condom; " \
                         "below reorder level Micro-G"
        third_message = "Dear stella, these items are stocked out: mc. these items need to be reordered: mg. " \
                        "Please order mc 22 mg 40."
        fifth_message = "Dear super, Test RMS is experiencing the following problems: " \
                        "stockouts Male Condom; below reorder level Micro-G"
        last_message = "Dear stella, these items are stocked out: mc. these items need to be reordered: mg. " \
                       "Please order mc 22 mg 40."
        a = """
           5551234 > soh mc 0.0 mg 1.0 ng 25.0
           222222 < %s
           5551234 < %s
           5551234 > soh mc 0.2 mg 1.0
           222222 < %s
           5551234 < %s
           """ % (second_message, third_message, fifth_message, last_message)
        self.run_script(a)

    def test_combined4(self):
        second_message = "Dear super, Test RMS is experiencing the following problems: stockouts Male Condom; " \
                         "below reorder level Micro-G"
        last_message = "Dear stella, these items are stocked out: mc. these items need to be reordered: mg. " \
                       "Please order mc 22 mg 40."
        a = """
           5551234 > soh mc 0.0 mg 1.0 ng 60.0
           222222 < %s
           5551234 < %s
           """ % (second_message, last_message)
        self.run_script(a)

    def test_combined5(self):
        a = """
           5551234 > soh mc 25.0 lf 50.0 mg 300.0
           222222 < Dear super, Test RMS is experiencing the following problems: overstocked Micro-G
           5551234 < Dear stella, these items are overstocked: mg. The district admin has been informed.
           """
        self.run_script(a)

    def test_incomplete_report(self):
        assign_products_to_location()
        a = """
            5551234 > soh mg 31.0
            5551234 < Dear stella, still missing jd ng.
            5551234 > soh jd 25.0
            5551234 < Dear stella, still missing ng.
            5551234 > soh ng 25.0
            5551234 < Dear stella, thank you for reporting the commodities you have in stock.
        """
        self.run_script(a)
        restore_location_products()

    def test_incomplete_report2(self):
        assign_products_to_location()
        a = """
            5551234 > soh mg 25.0 jd 25.0 ng 25.0
            5551234 < Dear stella, thank you for reporting the commodities you have in stock.
        """
        self.run_script(a)
        restore_location_products()
