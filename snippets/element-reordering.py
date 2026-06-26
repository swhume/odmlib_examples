"""
element-reordering.py

ODM and Define-XML constrain the ORDER in which child elements may appear (the XSD uses
xs:sequence). When you build objects in code it is easy to add children in the wrong order --
for example, appending an Alias before setting the Description and Question on an ItemDef.

odmlib v0.2.0 lets you:
  1. detect an out-of-order object with `verify_order()`, which raises `OdmlibElementOrderError`
  2. fix it automatically with `reorder_object()`, which sorts children into schema sequence
     (and issues a warning so the change is visible)
  3. confirm the fix by calling `verify_order()` again

This snippet demonstrates that detect -> reorder -> re-verify workflow.
"""
import warnings
import odmlib.odm_1_3_2.model as ODM
from odmlib import OdmlibElementOrderError


def build_out_of_order_item_def():
    """Build an ItemDef whose children are added in the wrong order.

    The ItemDef schema sequence is Description, Question, ... , Alias. Here the Alias elements
    are appended first, so the object's child order violates the schema.
    """
    itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
    itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
    itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
    itd.Description = ODM.Description()
    itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
    itd.Question = ODM.Question()
    itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
    return itd


def main():
    itd = build_out_of_order_item_def()

    # --- 1. detect the out-of-order children ----------------------------------------------
    print("Step 1: verify element order on the freshly built ItemDef")
    try:
        itd.verify_order()
    except OdmlibElementOrderError as ve:
        print(f"  Detected invalid ItemDef element order: {ve}")
        reordered = True
    else:
        print("  ItemDef element order is already valid (nothing to fix)")
        reordered = False

    # --- 2. reorder the children into schema sequence -------------------------------------
    if reordered:
        print("\nStep 2: reorder_object() to fix the sequence")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            itd.reorder_object()
            if caught:
                print(f"  Warning issued during reorder: {caught[0].message}")

    # --- 3. re-verify -------------------------------------------------------------------
    print("\nStep 3: verify element order again")
    try:
        itd.verify_order()
    except OdmlibElementOrderError as ve:
        print(f"  Element order still invalid: {ve}")
    else:
        print("  Element order fixed: ItemDef now conforms to the schema sequence")

    # the reordered object serializes with children in the correct order
    print("\nReordered ItemDef as XML:")
    print(f"  {itd.to_xml().attrib}  (children now: Description, Question, Alias, Alias)")


if __name__ == "__main__":
    main()
