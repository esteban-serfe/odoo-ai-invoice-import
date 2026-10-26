/** @odoo-module **/

import { attr } from "@mail/model/model_field";
import { registerPatch } from "@mail/model/model_core";
import { session } from "@web/session";

registerPatch({
  name: "Chatter",
  fields: {
    isLLMChatterUser: attr({
      compute() {
        return Boolean(session.llm_chatter_user);
      },
    }),
  },
});
